#!/usr/bin/env python3
"""Offline QEDR umem API-selection and page-count regression tests.

Run with: python3 tests/test_qedr_umem_compat.py

Only the feature-probe identifier/options and the two compatibility macro
definitions are read from driver sources. No Makefile or repository runner is
executed. A fixed grep invocation reads mock headers; a fixed user-space C
compiler builds a mock-only shared library in a new temporary directory. Its
test entry point performs only arithmetic and has no device or network API.
"""

import ctypes
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
DRIVER = ROOT / "qedr-8.70.12.0" / "src"
GREP = "/usr/bin/grep"
COMPILER = "/usr/bin/cc"
LIBRARY_FLAGS = ["-bundle"] if sys.platform == "darwin" else ["-shared"]

# Explicit interval counts, independently checked at 4 KiB and 64 KiB
# boundaries. The unaligned short range crosses only a 4 KiB boundary, while
# the last-byte range crosses both kinds of boundary.
CASES = (
    ("one_byte", 0x100000, 1, 1, 1),
    ("one_firmware_page", 0x100000, 4096, 1, 1),
    ("unaligned_short", 0x100123, 4000, 2, 1),
    ("last_byte_boundary", 0x10FFFF, 2, 2, 2),
    ("unaligned_many_pages", 0x100123, 3 * 65536 + 9000, 51, 4),
    ("aligned_many_pages", 0x100000, 2 * 65536, 32, 2),
)


class QedrUmemCompatTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        makefile = (DRIVER / "Makefile").read_text(encoding="utf-8")
        # Parse only a tightly constrained grep form. Never evaluate Make
        # syntax or run a command extracted from repository text.
        probes = re.findall(
            r'^ifneq \(\$\(shell grep (?P<word>-w )?'
            r'"(?P<identifier>[A-Za-z_][A-Za-z_0-9]*)" '
            r'\$\(ib_umem_h\) > /dev/null 2>&1 && echo '
            r'[A-Za-z_][A-Za-z_0-9]*\),\)\n'
            r'[ \t]+override EXTRA_CFLAGS \+= -D_HAS_UMEM_DMA_BLOCK\n'
            r'endif$',
            makefile,
            flags=re.MULTILINE,
        )
        if len(probes) != 1:
            raise AssertionError("Expected one supported umem feature probe")
        word, cls.probe_identifier = probes[0]
        cls.probe_options = ["-w"] if word else []

        compat = (DRIVER / "qedr_compat.h").read_text(encoding="utf-8")
        start = compat.index("#ifdef _HAS_UMEM_DMA_BLOCK /* QEDR_UPSTREAM */")
        end = compat.index("#ifdef _HAS_ALLOC_MW_V3", start)
        cls.compat_macros = compat[start:end]

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="qedr-umem-test-")
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        # Do not inherit compiler options, launchers, include paths, SDK
        # overrides, or library-search variables from the caller.
        self.environment = {
            "PATH": "/usr/bin:/bin",
            "TMPDIR": str(self.directory),
            "LANG": "C",
            "LC_ALL": "C",
        }

    def run_local(self, arguments):
        return subprocess.run(
            arguments,
            cwd=self.directory,
            env=self.environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )

    def probe(self, header):
        header_path = self.directory / "ib_umem.h"
        header_path.write_text(header, encoding="utf-8")
        result = self.run_local(
            [GREP, *self.probe_options, "--", self.probe_identifier, str(header_path)]
        )
        self.assertIn(result.returncode, (0, 1), result.stderr)
        return result.returncode == 0

    def test_probe_ignores_a_different_identifier_with_the_same_prefix(self):
        self.assertFalse(
            self.probe("static int ib_umem_num_dma_blocks_removed(void);\n")
        )

    def test_available_apis_compile_and_preserve_page_count_units(self):
        profiles = (
            "modern_without_iterator",  # Ubuntu 7.0.0-31 API shape
            "modern_with_iterator",     # Ubuntu 7.0.0-30 API shape
            "legacy_no_page_param",
        )
        for profile in profiles:
            for page_shift in (12, 16):
                with self.subTest(profile=profile, page_shift=page_shift):
                    self.compile_and_check(profile, page_shift)

    def compile_and_check(self, profile, page_shift):
        modern = profile.startswith("modern_")
        header = """
#include <stddef.h>
struct ib_umem {
    unsigned long address;
    unsigned long length;
};
"""
        if modern:
            # Expose only the modern counting API. A mistaken fallback is a
            # compile error, as on kernels that removed ib_umem_page_count.
            # Model one contiguous DMA interval, with IOVA equal to address:
            # this checks wrapper units, not kernel DMA mapping behavior.
            header += """
static size_t ib_umem_num_dma_blocks(struct ib_umem *umem,
                                    unsigned long page_size)
{
    unsigned long start = umem->address & ~(page_size - 1);
    unsigned long end = (umem->address + umem->length + page_size - 1)
                        & ~(page_size - 1);
    return (end - start) / page_size;
}
"""
            if profile == "modern_with_iterator":
                header += "#define rdma_umem_for_each_dma_block(...) unused\n"
        else:
            # Older umem page_count reports pinned system pages. Queue PBL
            # entries then expand those pages into firmware-page units.
            header += """
static size_t ib_umem_page_count(struct ib_umem *umem)
{
    return (umem->address % PAGE_SIZE + umem->length + PAGE_SIZE - 1)
           / PAGE_SIZE;
}
"""

        selected_modern = self.probe(header)
        definitions = [
            "#define FW_PAGE_SHIFT 12",
            "#define FW_PAGE_SIZE (1UL << FW_PAGE_SHIFT)",
            f"#define PAGE_SHIFT {page_shift}",
            "#define PAGE_SIZE (1UL << PAGE_SHIFT)",
            "#define DEFINE_IB_UMEM_NO_PAGE_PARAM",
        ]
        if selected_modern:
            definitions.append("#define _HAS_UMEM_DMA_BLOCK")
        calls = []
        for index, (_, address, length, pages_4k, pages_64k) in enumerate(CASES, 1):
            mr_pages = pages_4k if page_shift == 12 else pages_64k
            queue_pages = pages_4k if modern else mr_pages * (1 << (page_shift - 12))
            calls.append(
                f"    check_case({index}, {address}UL, {length}UL, "
                f"{queue_pages}UL, {mr_pages}UL);"
            )

        program = "\n".join(definitions) + """
#include "ib_umem.h"
struct mock_info { size_t pages; int initialized; };
struct mock_mr { struct ib_umem *umem; struct mock_info info; };
static void init_mr_info(void *dev, struct mock_info *info,
                         size_t pages, int initialized)
{
    (void)dev;
    info->pages = pages;
    info->initialized = initialized;
}
""" + self.compat_macros + """
static int failures;
static void check_case(int index, unsigned long address,
                       unsigned long length, size_t expected_queue,
                       size_t expected_mr)
{
    struct ib_umem umem = { .address = address, .length = length };
    struct mock_mr value = { .umem = &umem };
    struct mock_mr *mr = &value;
    void *dev = NULL;
    size_t queue_pages = COMPAT_IB_UMEM_COUNT((&umem));
    COMPAT_INIT_MR_INFO(mr);
    if (!failures && (queue_pages != expected_queue ||
        mr->info.pages != expected_mr || mr->info.initialized != 1)) {
        failures = index;
    }
}
int run_checks(void)
{
    failures = 0;
CALLS
    return failures;
}
""".replace("CALLS", "\n".join(calls))
        source_path = self.directory / "umem_compat_test.c"
        # A library without libc dependencies also works when the local SDK
        # and system linker disagree about the SDK's library-stub format.
        binary_path = self.directory / f"{profile}_{page_shift}.so"
        source_path.write_text(program, encoding="utf-8")
        compiled = self.run_local(
            [COMPILER, "-std=c11", "-Wall", "-Wextra", "-Werror", "-pedantic",
             "-O0", *LIBRARY_FLAGS, "-fPIC", "-nostdlib",
             str(source_path), "-o", str(binary_path)]
        )
        self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
        library = ctypes.CDLL(str(binary_path))
        library.run_checks.argtypes = []
        library.run_checks.restype = ctypes.c_int
        result = library.run_checks()
        case = CASES[result - 1][0] if 1 <= result <= len(CASES) else "unknown"
        self.assertEqual(result, 0, f"Queue or MR page counts differ: {case}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
