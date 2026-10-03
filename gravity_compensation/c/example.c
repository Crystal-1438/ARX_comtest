/* SPDX-License-Identifier: LGPL-2.1-or-later */
#include "x5_gravity.h"
#include <stdio.h> /* Used by this example only, not by the calculation core. */

int main(void)
{
    const x5_real q[6] = {0, 0.2f, -0.3f, 0.1f, 0, 0};
    x5_real torque[6];
    int i;
    const int status = x5_gravity_compute(X5_MODEL_2025, q, NULL,
                                          X5_GRAVITY_SDK, torque);
    if (status != X5_GRAVITY_OK) return 1;
    for (i = 0; i < 6; ++i) printf("joint%d: %.12g N*m\n", i+1, (double)torque[i]);
    return 0;
}
