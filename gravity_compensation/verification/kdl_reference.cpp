// SPDX-License-Identifier: LGPL-2.1-or-later
// Offline comparison oracle: real KDL 1.5.1 and optionally the pinned ARX math
// method. Never constructs InterfacesPy/ControllerBase or invokes CAN functions.
#include "chaindynparam.hpp"
#include <array>
#include <cstddef>
#include <cstring>
#include <dlfcn.h>
#include <iomanip>
#include <iostream>
#include <stdexcept>
#include <string>

static KDL::Vector read_vector() {
    double x, y, z;
    if (!(std::cin >> x >> y >> z)) throw std::runtime_error("invalid vector");
    return KDL::Vector(x, y, z);
}

int main(int argc, char** argv) {
    try {
        unsigned int count;
        if (!(std::cin >> count)) throw std::runtime_error("missing segment count");
        KDL::Chain chain;
        for (unsigned int i = 0; i < count; ++i) {
            int kind;
            std::cin >> kind;
            const auto xyz = read_vector();
            const auto rpy = read_vector();
            const auto axis = read_vector();
            double mass;
            std::cin >> mass;
            const auto com = read_vector();
            const KDL::Frame origin(KDL::Rotation::RPY(rpy.x(), rpy.y(), rpy.z()), xyz);
            // Same URDF -> KDL construction as kdl_parser::toKdl/addChildrenToTree.
            const auto name = "joint" + std::to_string(i);
            const KDL::Joint joint = kind == 0 ? KDL::Joint(name, KDL::Joint::Fixed)
                : KDL::Joint(name, xyz, origin.M * axis,
                             kind == 1 ? KDL::Joint::RotAxis : KDL::Joint::TransAxis);
            chain.addSegment(KDL::Segment("link" + std::to_string(i), joint, origin,
                                           KDL::RigidBodyInertia(mass, com)));
        }
        const auto gravity = read_vector();
        KDL::ChainDynParam dynamics(chain, gravity);
        const auto joints = chain.getNrOfJoints();
        KDL::JntArray q(joints), torque(joints);

        // Test-only x86_64 ABI adapter for the specific hashed vendor binary.
        // Disassembly shows the math method only reads nj at +0xc8 and a
        // ChainDynParam* at +0xf8. It never touches hardware/controller state.
        using VendorMath = KDL::JntArray (*)(void*, const KDL::JntArray&);
        VendorMath vendor = nullptr;
        alignas(std::max_align_t) std::array<unsigned char, 0x118> storage{};
        if (argc == 2) {
            if (sizeof(void*) != 8 || joints != 6)
                throw std::runtime_error("vendor probe requires x86_64 and 6 joints");
            void* handle = dlopen(argv[1], RTLD_LAZY | RTLD_LOCAL);
            if (!handle) throw std::runtime_error(dlerror());
            vendor = reinterpret_cast<VendorMath>(dlsym(handle,
                "_ZN3arx22KinematicDynamicSolver32computeGravityCompensationTorqueERKN3KDL8JntArrayE"));
            if (!vendor) throw std::runtime_error(dlerror());
            auto* ptr = &dynamics;
            std::memcpy(storage.data() + 0xc8, &joints, sizeof(joints));
            std::memcpy(storage.data() + 0xf8, &ptr, sizeof(ptr));
            // Keep the dlopen handle until process exit; no controller lifetime.
        }
        std::cout << std::setprecision(17);
        unsigned int cases;
        if (!(std::cin >> cases)) throw std::runtime_error("missing case count");
        for (unsigned int row = 0; row < cases; ++row) {
            for (unsigned int j = 0; j < joints; ++j)
                if (!(std::cin >> q(j))) throw std::runtime_error("incomplete q");
            if (dynamics.JntToGravity(q, torque) != 0)
                throw std::runtime_error("KDL JntToGravity failed");
            if (vendor) torque = vendor(storage.data(), q);
            for (unsigned int j = 0; j < joints; ++j)
                std::cout << (j ? " " : "") << torque(j);
            std::cout << '\n';
        }
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
