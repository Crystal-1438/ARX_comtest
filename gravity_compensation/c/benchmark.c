/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Host CPU-time benchmark only; stdio/time are NOT used by the C core.
 * Compile without LTO, so the repeated function calls cannot be folded.
 */
#include "x5_gravity.h"
#include <stdio.h>
#include <time.h>

int main(void)
{
    const float q[6] = {0, 0.2f, -0.3f, 0.1f, 0.4f, -0.2f};
    const float sine[6] = {0, 0.198669331f, -0.295520207f, 0.0998334166f, 0.389418342f, -0.198669331f};
    const float cosine[6] = {1, 0.980066578f, 0.955336489f, 0.995004165f, 0.921060994f, 0.980066578f};
    const unsigned iterations = 1000000;
    volatile float checksum = 0;
    float out[6];
    unsigned i;
    clock_t start = clock();
    double regular_ns, cached_ns;
    for (i = 0; i < iterations; ++i) {
        if (x5_gravity_compute(X5_MODEL_2025, q, 0, X5_GRAVITY_SDK, out)) return 1;
        checksum += out[i % 6];
    }
    regular_ns = 1e9*(double)(clock()-start)/CLOCKS_PER_SEC/iterations;
    start = clock();
    for (i = 0; i < iterations; ++i) {
        if (x5_gravity_compute_sincos(X5_MODEL_2025, sine, cosine, 0, X5_GRAVITY_SDK, out)) return 1;
        checksum += out[i % 6];
    }
    cached_ns = 1e9*(double)(clock()-start)/CLOCKS_PER_SEC/iterations;
    printf("host only; warm-cache calls; includes loop/checksum overhead\n");
    printf("angle input: %.2f ns/call\nprecomputed sincos: %.2f ns/call\n", regular_ns, cached_ns);
    printf("checksum: %.3f\n", (double)checksum);
    return 0;
}
