#!/usr/bin/env python3
"""Validate the real attention tables and initialization in a user-space mock.

Run on Linux with: python3 -B tests/test_qed_attention_bounds.py
No driver Makefile or device operation is run. All compiler outputs are
temporary. Callback addresses in the tables point to inert mock functions.
Invalid table data is rejected by a bounded validator before initialization.
"""

from pathlib import Path
import re
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def extract_function(source, name):
    match = re.search(r"^static void " + name + r"\(.*?^\}", source,
                      re.MULTILINE | re.DOTALL)
    if not match:
        raise AssertionError("Missing function: " + name)
    return match.group(0)


class AttentionTableTest(unittest.TestCase):
    def test_all_registers_and_chip_variants(self):
        source = (ROOT / "qed-8.70.12.0/src/qed_int.c").read_text()
        types = source[source.index("struct aeu_invert_reg_bit {"):
                       source.index("static int qed_mcp_attn_cb")]
        tables = source[source.index("enum aeu_invert_reg_special_type {"):
                        source.index("static struct aeu_invert_reg_bit *qed_int_aeu_translate")]
        translation = source[source.index("static struct aeu_invert_reg_bit *qed_int_aeu_translate"):
                             source.index("#define ATTN_STATE_BITS")]
        callbacks = sorted(set(re.findall(r"\bqed_\w+\b", tables)))
        blocks = sorted(set(re.findall(r"\b(?:BLOCK_\w+|MAX_BLOCK_ID)\b", tables)))
        preamble = r"""
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>
#include <stdio.h>
#include <string.h>
typedef uint32_t u32;
typedef uintptr_t dma_addr_t;
struct qed_hwfn;
#define BIT(n) (1UL << (n))
#define ARRAY_SIZE(a) (sizeof(a) / sizeof((a)[0]))
#define GET_FIELD(v, f) (((v) >> f##_SHIFT) & f##_MASK)
#define FIELD_VALUE(f, v) (((v) & f##_MASK) << f##_SHIFT)
#define QED_IS_BB(dev) ((dev)->bb)
#define DP_VERBOSE(...) ((void)0)
#define MISC_REG_AEU_GENERAL_ATTN_0 0x1000
"""
        preamble += "enum block_id { " + ", ".join(blocks) + " };\n"
        preamble += "\n".join(
            "static int " + name + "(struct qed_hwfn *hwfn) { (void)hwfn; return 0; }"
            for name in callbacks
        )
        mock = r"""
struct qed_dev { bool bb; };
struct qed_ptt { int unused; };
struct qed_sb_attn_info {
    void *sb_attn;
    dma_addr_t sb_phys;
    struct aeu_invert_reg *p_aeu_desc;
    u32 parity_mask[NUM_ATTN_REGS];
    u32 mfw_attn_addr;
};
struct qed_hwfn {
    struct qed_dev *cdev;
    struct qed_sb_attn_info *p_sb_attn;
    unsigned int rel_pf_id;
};
static void qed_int_sb_attn_setup(struct qed_hwfn *hwfn, struct qed_ptt *ptt)
{ (void)hwfn; (void)ptt; }
"""
        program = (preamble + types + tables + mock + translation +
                   extract_function(source, "qed_int_sb_attn_init") + CHECKS)
        with tempfile.TemporaryDirectory(prefix="qed-attention-test-") as temporary:
            directory = Path(temporary)
            c_file = directory / "attention.c"
            executable = directory / "attention-test"
            c_file.write_text(program)
            environment = {"PATH": "/usr/bin:/bin", "LANG": "C", "LC_ALL": "C",
                           "TMPDIR": temporary}
            compiled = subprocess.run(
                ["/usr/bin/cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 "-O1", "-fsanitize=undefined", "-fno-sanitize-recover=all",
                 str(c_file), "-o", str(executable)], cwd=directory,
                env=environment, capture_output=True, text=True, timeout=30,
            )
            self.assertEqual(compiled.returncode, 0, compiled.stdout + compiled.stderr)
            result = subprocess.run([str(executable)], cwd=directory,
                                    env=environment, capture_output=True,
                                    text=True, timeout=10)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual(result.stderr, "")


CHECKS = r"""
/* Hardware attention masks are independent expectations, not derived output. */
static const u32 expected[2][9] = {
    {0, 4, 0, 0x55435050, 0x55555555, 0x55555555, 0x55555555, 0x07f55555, 5},
    {0, 4, 0, 0x55435000, 0x55555555, 0x55555555, 0x55555555, 0x07f55555, 13}
};

static int validate(struct qed_hwfn *hwfn)
{
    for (size_t row = 0; row < ARRAY_SIZE(aeu_descs); row++) {
        unsigned int width = 0;
        for (size_t item = 0; item < ARRAY_SIZE(aeu_descs[row].bits) && width < 32; item++) {
            struct aeu_invert_reg_bit *bit = &aeu_descs[row].bits[item];
            unsigned int length = ATTENTION_LENGTH(bit->flags);
            if (!length || length > 32 - width)
                return 1;
            if (bit->flags & ATTENTION_BB_DIFFERENT)
                if (GET_FIELD(bit->flags, ATTENTION_BB) >= ARRAY_SIZE(aeu_descs_special))
                    return 2;
            if (ATTENTION_LENGTH(qed_int_aeu_translate(hwfn, bit)->flags) != length)
                return 3;
            width += length;
        }
        if (width != 32)
            return 4;
    }
    return 0;
}

int main(void)
{
    struct qed_dev dev = {0};
    struct qed_sb_attn_info sb = {0};
    struct qed_hwfn hwfn = {&dev, &sb, 3};
    for (unsigned int bb = 0; bb < 2; bb++) {
        dev.bb = bb;
        if (validate(&hwfn)) {
            fprintf(stderr, "Attention table must cover exactly 32 bits per register\n");
            return 1;
        }
        qed_int_sb_attn_init(&hwfn, NULL, &sb, 0x12340000);
        if (memcmp(sb.parity_mask, expected[bb], sizeof(sb.parity_mask)))
            return 2;
        if (sb.sb_attn != &sb || sb.sb_phys != 0x12340000 ||
            sb.p_aeu_desc != aeu_descs || sb.mfw_attn_addr != 0x1018)
            return 3;
    }
    /* Reject the original truncated description without walking beyond it. */
    unsigned int saved = aeu_descs[8].bits[7].flags;
    aeu_descs[8].bits[7].flags = FIELD_VALUE(ATTENTION_LENGTH, 9);
    int rejected = validate(&hwfn);
    aeu_descs[8].bits[7].flags = saved;
    if (!rejected || validate(&hwfn))
        return 4;
    return 0;
}
"""


if __name__ == "__main__":
    unittest.main(verbosity=2)
