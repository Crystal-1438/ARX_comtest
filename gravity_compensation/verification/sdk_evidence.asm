# ARX X5 fixed x86_64 library gravity evidence
# SHA256 cb51e1acfccd1e904ca263d45db2035fb33a457ded0b64e5376a864aaf1abeb5
# objdump -d -C --no-show-raw-insn; below are selected virtual-address ranges

vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so:     file format elf64-x86-64


Disassembly of section .text:

0000000000013860 <arx::x5::ControllerBase::stateGravityCompensation()>:
   13860:	endbr64
   13864:	mov    0x4b8(%rdi),%rdx
   1386b:	mov    0xc8(%rdi),%rax
   13872:	pxor   %xmm0,%xmm0
   13876:	movq   $0x0,0x18(%rax)
   1387e:	movq   $0x0,0x20(%rax)
   13886:	movups %xmm0,(%rax)
   13889:	movsd  (%rdx),%xmm0
   1388d:	movq   $0x0,0x40(%rax)
   13895:	movq   $0x0,0x48(%rax)
   1389d:	movq   $0x0,0x28(%rax)
   138a5:	movq   $0x0,0x30(%rax)
   138ad:	movsd  %xmm0,0x10(%rax)
   138b2:	movsd  0x8(%rdx),%xmm0
   138b7:	movq   $0x0,0x68(%rax)
   138bf:	movq   $0x0,0x70(%rax)
   138c7:	movq   $0x0,0x50(%rax)
   138cf:	movq   $0x0,0x58(%rax)
   138d7:	movsd  %xmm0,0x38(%rax)
   138dc:	movsd  0x10(%rdx),%xmm0
   138e1:	movq   $0x0,0x90(%rax)
   138ec:	movq   $0x0,0x98(%rax)
   138f7:	movq   $0x0,0x78(%rax)
   138ff:	movq   $0x0,0x80(%rax)
   1390a:	movsd  %xmm0,0x60(%rax)
   1390f:	movsd  0x18(%rdx),%xmm0
   13914:	movq   $0x0,0xb8(%rax)
   1391f:	movq   $0x0,0xc0(%rax)
   1392a:	movq   $0x0,0xa0(%rax)
   13935:	movq   $0x0,0xa8(%rax)
   13940:	movsd  %xmm0,0x88(%rax)
   13948:	movsd  0x20(%rdx),%xmm0
   1394d:	movq   $0x0,0xe0(%rax)
   13958:	movsd  %xmm0,0xb0(%rax)
   13960:	movq   $0x0,0xe8(%rax)
   1396b:	movq   $0x0,0xc8(%rax)
   13976:	movq   $0x0,0xd0(%rax)
   13981:	movsd  0x28(%rdx),%xmm0
   13986:	movsd  %xmm0,0xd8(%rax)
   1398e:	mov    0x188(%rdi),%rax
   13995:	movsd  (%rax),%xmm0
   13999:	movsd  %xmm0,0x78(%rdi)
   1399e:	movsd  0x20(%rax),%xmm0
   139a3:	movsd  %xmm0,0x80(%rdi)
   139ab:	movsd  0x40(%rax),%xmm0
   139b0:	movsd  %xmm0,0x88(%rdi)
   139b8:	movsd  0x60(%rax),%xmm0
   139bd:	movsd  %xmm0,0x90(%rdi)
   139c5:	movsd  0x80(%rax),%xmm0
   139cd:	movsd  %xmm0,0x98(%rdi)
   139d5:	movsd  0xa0(%rax),%xmm0
   139dd:	movsd  %xmm0,0xa0(%rdi)
   139e5:	jmp    10590 <arx::x5::ControllerBase::CatchSoft()@plt>
   139ea:	nopw   0x0(%rax,%rax,1)


vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so:     file format elf64-x86-64


Disassembly of section .text:

00000000000153d0 <arx::x5::ControllerBase::read()+0x130>:
   153d0:	lea    0x10(%rsp),%r12
   153d5:	mov    $0x6,%esi
   153da:	xor    %ebp,%ebp
   153dc:	mov    %r12,%rdi
   153df:	call   10f50 <KDL::JntArray::JntArray(unsigned int)@plt>
   153e4:	nopl   0x0(%rax)
   153e8:	mov    %rbp,%rax
   153eb:	xor    %edx,%edx
   153ed:	mov    %ebp,%esi
   153ef:	mov    %r12,%rdi
   153f2:	shl    $0x5,%rax
   153f6:	add    0x188(%rbx),%rax
   153fd:	movsd  (%rax),%xmm3
   15401:	movsd  %xmm3,0x8(%rsp)
   15407:	call   11270 <KDL::JntArray::operator()(unsigned int, unsigned int)@plt>
   1540c:	movsd  0x8(%rsp),%xmm3
   15412:	add    $0x1,%rbp
   15416:	movsd  %xmm3,(%rax)
   1541a:	cmp    $0x6,%rbp
   1541e:	jne    153e8 <arx::x5::ControllerBase::read()+0x148>
   15420:	lea    0x298(%rbx),%r14
   15427:	lea    0x20(%rsp),%r13
   1542c:	mov    %r12,%rdx
   1542f:	mov    %r14,%rsi
   15432:	mov    %r13,%rdi
   15435:	call   10f60 <arx::KinematicDynamicSolver::computeGravityCompensationTorque(KDL::JntArray const&)@plt>
   1543a:	xor    %ebp,%ebp
   1543c:	nopl   0x0(%rax)
   15440:	xor    %edx,%edx
   15442:	mov    %ebp,%esi
   15444:	mov    %r13,%rdi
   15447:	call   11270 <KDL::JntArray::operator()(unsigned int, unsigned int)@plt>
   1544c:	movsd  (%rax),%xmm0
   15450:	mov    0x4b8(%rbx),%rax
   15457:	movsd  %xmm0,(%rax,%rbp,8)
   1545c:	add    $0x1,%rbp
   15460:	cmp    $0x6,%rbp
   15464:	jne    15440 <arx::x5::ControllerBase::read()+0x1a0>


vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so:     file format elf64-x86-64


Disassembly of section .text:

0000000000015d74 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0x4a4>:
   15d74:	mov    %r13d,0x258(%rbx)
   15d7b:	mov    %r12,%rcx
   15d7e:	lea    0x100(%rsp),%r13
   15d86:	movabs $0x6e696c5f65736162,%rax
   15d90:	movups %xmm0,0x280(%rbx)
   15d97:	lea    0x80(%rsp),%rdx
   15d9f:	movl   $0xc8,0x278(%rbx)
   15da9:	movq   $0x0,0x290(%rbx)
   15db4:	mov    %r13,0xf0(%rsp)
   15dbc:	movl   $0x6b6e696c,0x100(%rsp)
   15dc7:	movb   $0x36,0x104(%rsp)
   15dcf:	movq   $0x5,0xf8(%rsp)
   15ddb:	movb   $0x0,0x105(%rsp)
   15de3:	mov    %r14,0x80(%rsp)
   15deb:	mov    %rax,0x90(%rsp)
   15df3:	movb   $0x6b,0x98(%rsp)
   15dfb:	movq   $0x9,0x88(%rsp)
   15e07:	movb   $0x0,0x99(%rsp)
   15e0f:	call   108a0 <arx::KinematicDynamicSolver::KinematicDynamicSolver(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&)@plt>


vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so:     file format elf64-x86-64


Disassembly of section .text:

000000000002c120 <arx::KinematicDynamicSolver::computeGravityCompensationTorque(KDL::JntArray const&)>:
   2c120:	endbr64
   2c124:	push   %r13
   2c126:	push   %r12
   2c128:	mov    %rdi,%r12
   2c12b:	push   %rbp
   2c12c:	mov    %rdx,%rbp
   2c12f:	push   %rbx
   2c130:	mov    %rsi,%rbx
   2c133:	sub    $0x18,%rsp
   2c137:	mov    0xc8(%rsi),%esi
   2c13d:	call   10f50 <KDL::JntArray::JntArray(unsigned int)@plt>
   2c142:	mov    0xf8(%rbx),%rdi
   2c149:	mov    %r12,%rdx
   2c14c:	mov    %rbp,%rsi
   2c14f:	mov    (%rdi),%rax
   2c152:	call   *0x38(%rax)
   2c155:	test   %eax,%eax
   2c157:	js     2c1e8 <arx::KinematicDynamicSolver::computeGravityCompensationTorque(KDL::JntArray const&)+0xc8>
   2c15d:	xor    %ebx,%ebx
   2c15f:	xor    %edx,%edx
   2c161:	mov    %ebx,%esi
   2c163:	mov    %r12,%rdi
   2c166:	call   11270 <KDL::JntArray::operator()(unsigned int, unsigned int)@plt>
   2c16b:	movsd  0x6ee5(%rip),%xmm0        # 33058 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xad0>
   2c173:	mulsd  (%rax),%xmm0
   2c177:	xor    %edx,%edx
   2c179:	mov    %ebx,%esi
   2c17b:	mov    %r12,%rdi
   2c17e:	movsd  %xmm0,0x8(%rsp)
   2c184:	call   11270 <KDL::JntArray::operator()(unsigned int, unsigned int)@plt>
   2c189:	movsd  0x8(%rsp),%xmm0
   2c18f:	add    $0x1,%ebx
   2c192:	movsd  %xmm0,(%rax)
   2c196:	cmp    $0x3,%ebx
   2c199:	jne    2c15f <arx::KinematicDynamicSolver::computeGravityCompensationTorque(KDL::JntArray const&)+0x3f>
   2c19b:	xor    %edx,%edx
   2c19d:	mov    %ebx,%esi
   2c19f:	mov    %r12,%rdi
   2c1a2:	call   11270 <KDL::JntArray::operator()(unsigned int, unsigned int)@plt>
   2c1a7:	movsd  0x6eb1(%rip),%xmm1        # 33060 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xad8>
   2c1af:	mulsd  (%rax),%xmm1
   2c1b3:	xor    %edx,%edx
   2c1b5:	mov    %ebx,%esi
   2c1b7:	mov    %r12,%rdi
   2c1ba:	movsd  %xmm1,0x8(%rsp)
   2c1c0:	call   11270 <KDL::JntArray::operator()(unsigned int, unsigned int)@plt>
   2c1c5:	movsd  0x8(%rsp),%xmm1
   2c1cb:	add    $0x1,%ebx
   2c1ce:	movsd  %xmm1,(%rax)
   2c1d2:	cmp    $0x6,%ebx
   2c1d5:	jne    2c19b <arx::KinematicDynamicSolver::computeGravityCompensationTorque(KDL::JntArray const&)+0x7b>
   2c1d7:	add    $0x18,%rsp
   2c1db:	mov    %r12,%rax
   2c1de:	pop    %rbx
   2c1df:	pop    %rbp
   2c1e0:	pop    %r12
   2c1e2:	pop    %r13
   2c1e4:	ret


vendor/ARX_X5/py/arx_x5_python/bimanual/lib/arx_x5_src/libarx_x5_src.so:     file format elf64-x86-64


Disassembly of section .text:

000000000002c54f <arx::KinematicDynamicSolver::KinematicDynamicSolver(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&)+0x2cf>:
   2c54f:	movsd  0x6b21(%rip),%xmm0        # 33078 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xaf0>
   2c557:	pxor   %xmm1,%xmm1
   2c55b:	mov    $0x2b8,%edi
   2c560:	movups %xmm1,0x100(%rbx)
   2c567:	movsd  %xmm0,0x110(%rbx)
   2c56f:	movaps %xmm1,0x20(%rsp)
   2c574:	movsd  %xmm0,0x30(%rsp)
   2c57a:	call   10e00 <operator new(unsigned long)@plt>
   2c57f:	mov    0x8(%rsp),%rdx
   2c584:	mov    %r14,%rsi
   2c587:	mov    %rax,%rdi
   2c58a:	mov    %rax,%rbp
   2c58d:	call   10c60 <KDL::ChainDynParam::ChainDynParam(KDL::Chain const&, KDL::Vector)@plt>
   2c592:	mov    0xf8(%rbx),%rdi
   2c599:	mov    %rbp,0xf8(%rbx)
   2c5a0:	test   %rdi,%rdi
   2c5a3:	je     2c5ab <arx::KinematicDynamicSolver::KinematicDynamicSolver(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&)+0x32b>
   2c5a5:	mov    (%rdi),%rax
   2c5a8:	call   *0x8(%rax)

# These .rodata virtual addresses equal file offsets in this ELF:
# 0x33058: 9a9999999999e93f -> little-endian double 0.8
# 0x33060: 1f85eb51b81ef53f -> little-endian double 1.32
# 0x33078: 1f85eb51b89e23c0 -> little-endian double -9.81
