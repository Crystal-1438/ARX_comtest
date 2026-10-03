/* SPDX-License-Identifier: LGPL-2.1-or-later */
#ifndef X5_GRAVITY_H
#define X5_GRAVITY_H

/* Pure C99 float, no heap or runtime/library dependencies (not even libm).
 * All inputs use URDF/SDK coordinates; outputs are joint1..joint6, N*m.
 */
typedef float x5_real;

#define X5_GRAVITY_DOF 6
/* Bounded range reduction, deliberately not a general-purpose sin/cos API. */
#define X5_GRAVITY_MAX_ANGLE 128.0f

typedef enum {
    X5_MODEL_2023 = 0,
    X5_MODEL_MASTER = 1,
    X5_MODEL_2025 = 2
} x5_model;

typedef enum {
    X5_GRAVITY_PHYSICAL = 0, /* KDL's G(q) */
    X5_GRAVITY_SDK = 1       /* G(q) * [0.8,0.8,0.8,1.32,1.32,1.32] */
} x5_gravity_mode;

enum {
    X5_GRAVITY_OK = 0,
    X5_GRAVITY_INVALID_ARGUMENT = -1,
    X5_GRAVITY_ANGLE_RANGE = -2
};

#ifdef __cplusplus
extern "C" {
#endif

#ifndef X5_GRAVITY_NO_TRIG
/* q: six finite radians, |q[i]| <= MAX_ANGLE.
 * gravity_base: three finite m/s^2 in the base frame, or NULL for (0,0,-9.81).
 * torque: six writable elements. No output is written on a validation error.
 * Normal robot joint angles are far inside the supported range.
 */
int x5_gravity_compute(x5_model model, const x5_real q[6],
                       const x5_real gravity_base[3], x5_gravity_mode mode,
                       x5_real torque[6]);
#endif

/* Fastest path when sin(q)/cos(q) are already available from another loop.
 * Caller supplies consistent unit-circle pairs. The function checks finite
 * components in [-1,1], but does not recompute trigonometry or renormalize.
 * Define X5_GRAVITY_NO_TRIG to omit the angle-based entry point entirely.
 */
int x5_gravity_compute_sincos(x5_model model, const x5_real sin_q[6],
                              const x5_real cos_q[6], const x5_real gravity_base[3],
                              x5_gravity_mode mode, x5_real torque[6]);

#ifdef __cplusplus
}
#endif
#endif
