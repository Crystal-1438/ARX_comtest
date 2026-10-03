/* SPDX-License-Identifier: LGPL-2.1-or-later
 * Static specialization of KDL RNE; original algorithm (C) 2009 Ruben Smits
 * and Dominick Vanthienen. Modified 2026-10-03: X5-specific C99 implementation,
 * subtree first-moment reduction, axis rotations, internal bounded sin/cos.
 */
#include "x5_gravity.h"
#include "x5_gravity_data.h"
#include <float.h>
#include <limits.h>

#if INT_MAX < 2147483647
#error "The built-in range reducer requires an int with at least 32 bits"
#endif
#if FLT_RADIX != 2 || FLT_MANT_DIG != 24
#error "This implementation is validated for binary32 float"
#endif

#define REAL_MAX FLT_MAX

typedef struct { x5_real x, y, z; } vec3;

static vec3 rx(vec3 v, x5_real s, x5_real c)
{
    vec3 r = {v.x, c*v.y - s*v.z, s*v.y + c*v.z};
    return r;
}

static vec3 ry(vec3 v, x5_real s, x5_real c)
{
    vec3 r = {c*v.x + s*v.z, v.y, -s*v.x + c*v.z};
    return r;
}

static vec3 rz(vec3 v, x5_real s, x5_real c)
{
    vec3 r = {c*v.x - s*v.y, s*v.x + c*v.y, v.z};
    return r;
}

static vec3 moment(const x5_real h[3], vec3 a, vec3 downstream)
{
    vec3 n = {downstream.x + h[1]*a.z - h[2]*a.y,
              downstream.y + h[2]*a.x - h[0]*a.z,
              downstream.z + h[0]*a.y - h[1]*a.x};
    return n;
}

static int valid_request(x5_model model, const x5_real g[3],
                         x5_gravity_mode mode, x5_real torque[6])
{
    int i;
    if ((unsigned)model > (unsigned)X5_MODEL_2025 || !torque ||
        (mode != X5_GRAVITY_PHYSICAL && mode != X5_GRAVITY_SDK))
        return 0;
    if (g)
        for (i = 0; i < 3; ++i)
            if (!(g[i] >= -REAL_MAX && g[i] <= REAL_MAX)) return 0;
    return 1;
}

#ifndef X5_GRAVITY_NO_TRIG
static void bounded_sincos(x5_real angle, x5_real *s, x5_real *c)
{
    /* Reduce to [-pi/4, pi/4] using only float and a small integer quadrant.
     * |angle| <= 128 -> |quadrant| <= 81: multiplication by 1.5703125f is
     * exact in float. Split pi/2 avoids cancellation from subtracting one
     * rounded large float constant. Polynomial remainder < 2.5e-8, below
     * float rounding. No double arithmetic, lookup table, heap or libm.
     */
    const x5_real scaled = angle * 0.63661977236758134308f;
    const int quadrant = (int)(scaled + (scaled >= 0.0f ? 0.5f : -0.5f));
    const x5_real x = (angle - (x5_real)quadrant * 1.5703125f)
                      - (x5_real)quadrant * 0.00048382679489661923f;
    const x5_real x2 = x*x;
    x5_real sp, cp, sv, cv;
    sp = 1.0f/362880.0f;
    cp = 1.0f/40320.0f;
    sp = -1.0f/5040.0f + x2*sp;
    sp = 1.0f/120.0f + x2*sp;
    sp = -1.0f/6.0f + x2*sp;
    cp = -1.0f/720.0f + x2*cp;
    cp = 1.0f/24.0f + x2*cp;
    cp = -1.0f/2.0f + x2*cp;
    sv = x + x*x2*sp;
    cv = (x5_real)1 + x2*cp;
    switch ((unsigned)quadrant & 3u) {
    case 0: *s = sv;  *c = cv;  break;
    case 1: *s = cv;  *c = -sv; break;
    case 2: *s = -sv; *c = -cv; break;
    default: *s = -cv; *c = sv; break;
    }
}
#endif

static void calculate(x5_model model, const x5_real s[6], const x5_real c[6],
                       const x5_real g[3], x5_gravity_mode mode, x5_real out[6])
{
    const x5_real (*h)[3] = x5_first_moments[model];
    const int vertical = !g || (g[0] == 0 && g[1] == 0);
    vec3 a1 = {0, 0, 9.81f};
    vec3 a2, a3, a4, a5, a6, n;
    const vec3 zero = {0, 0, 0};
    x5_real tau[6];
    int i;
    /* Joint6's fixed roll and its X rotation commute: fuse both rotations. */
    const x5_real s6 = X5_FIXED_ROLL_SIN*c[5] + X5_FIXED_ROLL_COS*s[5];
    const x5_real c6 = X5_FIXED_ROLL_COS*c[5] - X5_FIXED_ROLL_SIN*s[5];
    if (g) { a1.x = -g[0]; a1.y = -g[1]; a1.z = -g[2]; }
    if (!vertical) a1 = rz(a1, -s[0], c[0]);
    a2 = ry(a1, -s[1], c[1]);
    a3 = ry(rx(a2, -X5_FIXED_ROLL_SIN, X5_FIXED_ROLL_COS), -s[2], c[2]);
    a4 = ry(a3, -s[3], c[3]);
    a5 = rz(a4, -s[4], c[4]);
    a6 = rx(a5, -s6, c6);

    /* h_i = m_i*com_i + subtree_mass_(i+1)*joint_origin_(i+1).
     * Descendant force equals subtree_mass*(-gravity) in each frame, so no
     * per-link force vectors, force transforms or 3x3 matrices are needed.
     */
    n = moment(h[5], a6, zero); tau[5] = n.x;
    n = moment(h[4], a5, rx(n, s6, c6)); tau[4] = n.z;
    n = moment(h[3], a4, rz(n, s[4], c[4])); tau[3] = n.y;
    n = moment(h[2], a3, ry(n, s[3], c[3])); tau[2] = n.y;
    n = moment(h[1], a2, rx(ry(n, s[2], c[2]), X5_FIXED_ROLL_SIN, X5_FIXED_ROLL_COS));
    tau[1] = n.y;
    if (vertical) {
        /* Rotation about the gravity axis cannot change potential energy. */
        tau[0] = 0;
    } else {
        n = moment(h[0], a1, ry(n, s[1], c[1])); tau[0] = n.z;
    }
    for (i = 0; i < 6; ++i)
        out[i] = mode == X5_GRAVITY_SDK
            ? tau[i] * (i < 3 ? 0.8f : 1.32f) : tau[i];
}

#ifndef X5_GRAVITY_NO_TRIG
int x5_gravity_compute(x5_model model, const x5_real q[6], const x5_real g[3],
                       x5_gravity_mode mode, x5_real torque[6])
{
    x5_real s[6], c[6];
    int i;
    if (!q || !valid_request(model, g, mode, torque)) return X5_GRAVITY_INVALID_ARGUMENT;
    for (i = 0; i < 6; ++i)
        if (!(q[i] >= -X5_GRAVITY_MAX_ANGLE && q[i] <= X5_GRAVITY_MAX_ANGLE))
            return X5_GRAVITY_ANGLE_RANGE;
    s[0] = 0; c[0] = 1;
    /* Default installation: yaw has no gravity effect, so only 5 trig pairs. */
    i = (!g || (g[0] == 0 && g[1] == 0)) ? 1 : 0;
    for (; i < 6; ++i) bounded_sincos(q[i], &s[i], &c[i]);
    calculate(model, s, c, g, mode, torque);
    return X5_GRAVITY_OK;
}
#endif

int x5_gravity_compute_sincos(x5_model model, const x5_real s[6], const x5_real c[6],
                              const x5_real g[3], x5_gravity_mode mode, x5_real torque[6])
{
    int i;
    if (!s || !c || !valid_request(model, g, mode, torque)) return X5_GRAVITY_INVALID_ARGUMENT;
    for (i = 0; i < 6; ++i)
        if (!(s[i] >= -1 && s[i] <= 1 && c[i] >= -1 && c[i] <= 1))
            return X5_GRAVITY_INVALID_ARGUMENT;
    calculate(model, s, c, g, mode, torque);
    return X5_GRAVITY_OK;
}
