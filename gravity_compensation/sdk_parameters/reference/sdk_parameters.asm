0000000000012cd0 <arx::x5::ControllerBase::setHomePositions(std::vector<double, std::allocator<double> >)>:
   12cd0:	endbr64
   12cd4:	mov    (%rsi),%rdx
   12cd7:	mov    0x18(%rdi),%rax
   12cdb:	lea    0xf(%rdx),%rcx
   12cdf:	sub    %rax,%rcx
   12ce2:	cmp    $0x1e,%rcx
   12ce6:	jbe    12d08 <arx::x5::ControllerBase::setHomePositions(std::vector<double, std::allocator<double> >)+0x38>
   12ce8:	movupd (%rdx),%xmm1
   12cec:	movups %xmm1,(%rax)
   12cef:	movupd 0x10(%rdx),%xmm2
   12cf4:	movups %xmm2,0x10(%rax)
   12cf8:	movupd 0x20(%rdx),%xmm3
   12cfd:	movups %xmm3,0x20(%rax)
   12d01:	ret
   12d02:	nopw   0x0(%rax,%rax,1)
   12d08:	movsd  (%rdx),%xmm0
   12d0c:	movsd  %xmm0,(%rax)
   12d10:	movsd  0x8(%rdx),%xmm0
   12d15:	movsd  %xmm0,0x8(%rax)
   12d1a:	movsd  0x10(%rdx),%xmm0
   12d1f:	movsd  %xmm0,0x10(%rax)
   12d24:	movsd  0x18(%rdx),%xmm0
   12d29:	movsd  %xmm0,0x18(%rax)
   12d2e:	movsd  0x20(%rdx),%xmm0
   12d33:	movsd  %xmm0,0x20(%rax)
   12d38:	movsd  0x28(%rdx),%xmm0
   12d3d:	movsd  %xmm0,0x28(%rax)
   12d42:	ret
   12d43:	nop
   12d44:	data16 cs nopw 0x0(%rax,%rax,1)
   12d4f:	nop

0000000000012d50 <arx::x5::ControllerBase::stateGoHome()>:
   12d50:	endbr64
   12d54:	push   %r13
   12d56:	push   %r12
   12d58:	lea    0x78(%rdi),%r12
   12d5c:	push   %rbp
   12d5d:	mov    %rdi,%rbp
   12d60:	push   %rbx
   12d61:	xor    %ebx,%ebx
   12d63:	sub    $0x48,%rsp
   12d67:	mov    %fs:0x28,%rax
   12d70:	mov    %rax,0x38(%rsp)
   12d75:	xor    %eax,%eax
   12d77:	movb   $0x0,(%rdi)
   12d7a:	mov    %rsp,%r13
   12d7d:	nopl   (%rax)
   12d80:	mov    0x1f819(%rip),%rax        # 325a0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x18>
   12d87:	mov    0x18(%rbp),%rdi
   12d8b:	lea    0x0(%r13,%rbx,1),%rdx
   12d90:	lea    (%r12,%rbx,1),%rsi
   12d94:	movq   %rax,%xmm2
   12d99:	mov    0x1f808(%rip),%rax        # 325a8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x20>
   12da0:	add    %rbx,%rdi
   12da3:	add    $0x8,%rbx
   12da7:	movq   %rax,%xmm1
   12dac:	mov    0x1f7fd(%rip),%rax        # 325b0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x28>
   12db3:	movq   %rax,%xmm0
   12db8:	call   106f0 <arx::solve::Interpolation(double*, double*, double*, double, double, double)@plt>
   12dbd:	cmp    $0x30,%rbx
   12dc1:	jne    12d80 <arx::x5::ControllerBase::stateGoHome()+0x30>
   12dc3:	mov    0x4f8(%rbp),%rsi
   12dca:	mov    0xc8(%rbp),%rax
   12dd1:	mov    0x510(%rbp),%rcx
   12dd8:	mov    0x4b8(%rbp),%rdx
   12ddf:	movsd  (%rsi),%xmm0
   12de3:	movsd  %xmm0,0x18(%rax)
   12de8:	movsd  (%rcx),%xmm0
   12dec:	movsd  %xmm0,0x20(%rax)
   12df1:	movsd  0x78(%rbp),%xmm0
   12df6:	movsd  %xmm0,(%rax)
   12dfa:	movsd  (%rsp),%xmm0
   12dff:	movsd  %xmm0,0x8(%rax)
   12e04:	movsd  (%rdx),%xmm0
   12e08:	movsd  %xmm0,0x10(%rax)
   12e0d:	movsd  0x8(%rsi),%xmm0
   12e12:	movsd  %xmm0,0x40(%rax)
   12e17:	movsd  0x8(%rcx),%xmm0
   12e1c:	movsd  %xmm0,0x48(%rax)
   12e21:	movsd  0x80(%rbp),%xmm0
   12e29:	movsd  %xmm0,0x28(%rax)
   12e2e:	movsd  0x8(%rsp),%xmm0
   12e34:	movsd  %xmm0,0x30(%rax)
   12e39:	movsd  0x8(%rdx),%xmm0
   12e3e:	movsd  %xmm0,0x38(%rax)
   12e43:	movsd  0x10(%rsi),%xmm0
   12e48:	movsd  %xmm0,0x68(%rax)
   12e4d:	movsd  0x10(%rcx),%xmm0
   12e52:	movsd  %xmm0,0x70(%rax)
   12e57:	movsd  0x88(%rbp),%xmm0
   12e5f:	movsd  %xmm0,0x50(%rax)
   12e64:	movsd  0x10(%rsp),%xmm0
   12e6a:	movsd  %xmm0,0x58(%rax)
   12e6f:	movsd  0x10(%rdx),%xmm0
   12e74:	movsd  %xmm0,0x60(%rax)
   12e79:	movsd  0x18(%rsi),%xmm0
   12e7e:	movsd  %xmm0,0x90(%rax)
   12e86:	movsd  0x18(%rcx),%xmm0
   12e8b:	movsd  %xmm0,0x98(%rax)
   12e93:	movsd  0x90(%rbp),%xmm0
   12e9b:	movsd  %xmm0,0x78(%rax)
   12ea0:	movsd  0x18(%rsp),%xmm0
   12ea6:	movsd  %xmm0,0x80(%rax)
   12eae:	movsd  0x18(%rdx),%xmm0
   12eb3:	movsd  %xmm0,0x88(%rax)
   12ebb:	movsd  0x20(%rsi),%xmm0
   12ec0:	movsd  %xmm0,0xb8(%rax)
   12ec8:	movsd  0x20(%rcx),%xmm0
   12ecd:	movsd  %xmm0,0xc0(%rax)
   12ed5:	movsd  0x98(%rbp),%xmm0
   12edd:	movsd  %xmm0,0xa0(%rax)
   12ee5:	movsd  0x20(%rsp),%xmm0
   12eeb:	movsd  %xmm0,0xa8(%rax)
   12ef3:	movsd  0x20(%rdx),%xmm0
   12ef8:	movsd  %xmm0,0xb0(%rax)
   12f00:	movsd  0x28(%rsi),%xmm0
   12f05:	movsd  %xmm0,0xe0(%rax)
   12f0d:	movsd  0x28(%rcx),%xmm0
   12f12:	movsd  %xmm0,0xe8(%rax)
   12f1a:	movsd  0xa0(%rbp),%xmm0
   12f22:	movsd  %xmm0,0xc8(%rax)
   12f2a:	movsd  0x28(%rsp),%xmm0
   12f30:	movsd  %xmm0,0xd0(%rax)
   12f38:	movsd  0x28(%rdx),%xmm0
   12f3d:	movsd  %xmm0,0xd8(%rax)
   12f45:	mov    0x188(%rbp),%rdx
   12f4c:	mov    0x18(%rbp),%rcx
   12f50:	movapd 0x1f6a8(%rip),%xmm3        # 32600 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x78>
   12f58:	movapd 0x1f6b0(%rip),%xmm4        # 32610 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x88>
   12f60:	movupd (%rdx),%xmm0
   12f64:	movupd 0x20(%rdx),%xmm1
   12f69:	movupd (%rcx),%xmm6
   12f6d:	movapd 0x1f6ab(%rip),%xmm5        # 32620 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x98>
   12f75:	movhpd 0x30(%rdx),%xmm1
   12f7a:	movhpd 0x10(%rdx),%xmm0
   12f7f:	movupd 0x10(%rcx),%xmm7
   12f84:	unpcklpd %xmm1,%xmm0
   12f88:	movupd 0x30(%rdx),%xmm1
   12f8d:	movlpd 0x28(%rdx),%xmm1
   12f92:	subpd  %xmm6,%xmm0
   12f96:	movsd  0x1f612(%rip),%xmm6        # 325b0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x28>
   12f9e:	andpd  %xmm3,%xmm0
   12fa2:	movapd %xmm0,%xmm2
   12fa6:	movupd 0x10(%rdx),%xmm0
   12fab:	movlpd 0x8(%rdx),%xmm0
   12fb0:	cmpltpd %xmm4,%xmm2
   12fb5:	unpcklpd %xmm1,%xmm0
   12fb9:	movapd %xmm0,%xmm1
   12fbd:	andpd  %xmm3,%xmm1
   12fc1:	movapd %xmm1,%xmm0
   12fc5:	movupd 0x60(%rdx),%xmm1
   12fca:	cmpltpd %xmm5,%xmm0
   12fcf:	movhpd 0x70(%rdx),%xmm1
   12fd4:	pand   %xmm2,%xmm0
   12fd8:	movupd 0x40(%rdx),%xmm2
   12fdd:	movhpd 0x50(%rdx),%xmm2
   12fe2:	unpcklpd %xmm1,%xmm2
   12fe6:	movupd 0x50(%rdx),%xmm1
   12feb:	movlpd 0x48(%rdx),%xmm1
   12ff0:	subpd  %xmm7,%xmm2
   12ff4:	andpd  %xmm3,%xmm2
   12ff8:	cmpltpd %xmm4,%xmm2
   12ffd:	movupd 0x70(%rdx),%xmm4
   13002:	movlpd 0x68(%rdx),%xmm4
   13007:	unpcklpd %xmm4,%xmm1
   1300b:	andpd  %xmm3,%xmm1
   1300f:	cmpltpd %xmm5,%xmm1
   13014:	pand   %xmm2,%xmm1
   13018:	shufps $0x88,%xmm1,%xmm0
   1301c:	pand   0x1f60c(%rip),%xmm0        # 32630 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xa8>
   13024:	movdqa %xmm0,%xmm1
   13028:	psrldq $0x8,%xmm1
   1302d:	paddd  %xmm1,%xmm0
   13031:	movdqa %xmm0,%xmm1
   13035:	psrldq $0x4,%xmm1
   1303a:	paddd  %xmm1,%xmm0
   1303e:	movq   0x1f5fa(%rip),%xmm1        # 32640 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xb8>
   13046:	movd   %xmm0,%eax
   1304a:	movsd  0x80(%rdx),%xmm0
   13052:	subsd  0x20(%rcx),%xmm0
   13057:	andpd  %xmm1,%xmm0
   1305b:	comisd %xmm0,%xmm6
   1305f:	jbe    13081 <arx::x5::ControllerBase::stateGoHome()+0x331>
   13061:	movsd  0x88(%rdx),%xmm0
   13069:	movsd  0x1f547(%rip),%xmm2        # 325b8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x30>
   13071:	xor    %esi,%esi
   13073:	andpd  %xmm1,%xmm0
   13077:	comisd %xmm0,%xmm2
   1307b:	seta   %sil
   1307f:	add    %esi,%eax
   13081:	movsd  0xa0(%rdx),%xmm0
   13089:	subsd  0x28(%rcx),%xmm0
   1308e:	movsd  0x1f51a(%rip),%xmm7        # 325b0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x28>
   13096:	andpd  %xmm1,%xmm0
   1309a:	comisd %xmm0,%xmm7
   1309e:	jbe    130bf <arx::x5::ControllerBase::stateGoHome()+0x36f>
   130a0:	movsd  0xa8(%rdx),%xmm0
   130a8:	xor    %edx,%edx
   130aa:	andpd  %xmm0,%xmm1
   130ae:	movsd  0x1f502(%rip),%xmm0        # 325b8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x30>
   130b6:	comisd %xmm1,%xmm0
   130ba:	seta   %dl
   130bd:	add    %edx,%eax
   130bf:	cmp    $0x5,%eax
   130c2:	jle    130c8 <arx::x5::ControllerBase::stateGoHome()+0x378>
   130c4:	movb   $0x1,0x0(%rbp)
   130c8:	mov    0x38(%rsp),%rax
   130cd:	xor    %fs:0x28,%rax
   130d6:	jne    130e3 <arx::x5::ControllerBase::stateGoHome()+0x393>
   130d8:	add    $0x48,%rsp
   130dc:	pop    %rbx
   130dd:	pop    %rbp
   130de:	pop    %r12
   130e0:	pop    %r13
   130e2:	ret
   130e3:	call   10ec0 <__stack_chk_fail@plt>
   130e8:	nopl   0x0(%rax,%rax,1)

00000000000130f0 <arx::x5::ControllerBase::CatchPositionCtrl()>:
   130f0:	endbr64
   130f4:	mov    0x18(%rdi),%rax
   130f8:	mov    0xb0(%rdi),%rcx
   130ff:	mov    0x188(%rdi),%rdx
   13106:	cmpl   $0x1,0x170(%rdi)
   1310d:	movsd  0x30(%rax),%xmm0
   13112:	movsd  0xc0(%rcx),%xmm1
   1311a:	movsd  0xc0(%rdx),%xmm3
   13122:	je     13250 <arx::x5::ControllerBase::CatchPositionCtrl()+0x160>
   13128:	addsd  %xmm1,%xmm0
   1312c:	movsd  0x1f484(%rip),%xmm2        # 325b8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x30>
   13134:	subsd  %xmm2,%xmm0
   13138:	subsd  %xmm3,%xmm0
   1313c:	mulsd  0x1f484(%rip),%xmm0        # 325c8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x40>
   13144:	movss  0x1f604(%rip),%xmm2        # 32750 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x1c8>
   1314c:	cvtsd2ss %xmm0,%xmm0
   13150:	comiss %xmm0,%xmm2
   13153:	ja     13248 <arx::x5::ControllerBase::CatchPositionCtrl()+0x158>
   13159:	comiss 0x1f5f4(%rip),%xmm0        # 32754 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x1cc>
   13160:	ja     131a8 <arx::x5::ControllerBase::CatchPositionCtrl()+0xb8>
   13162:	cmpl   $0x2,0x258(%rdi)
   13169:	mov    0xc8(%rdi),%rax
   13170:	je     131c0 <arx::x5::ControllerBase::CatchPositionCtrl()+0xd0>
   13172:	mov    0x1f42f(%rip),%rsi        # 325a8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x20>
   13179:	pxor   %xmm1,%xmm1
   1317d:	cvtss2sd %xmm0,%xmm0
   13181:	movq   $0x0,0x108(%rax)
   1318c:	movups %xmm1,0xf0(%rax)
   13193:	mov    %rsi,0x110(%rax)
   1319a:	movsd  %xmm0,0x100(%rax)
   131a2:	ret
   131a3:	nopl   0x0(%rax,%rax,1)
   131a8:	cmpl   $0x2,0x258(%rdi)
   131af:	movss  0x1f59d(%rip),%xmm0        # 32754 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x1cc>
   131b7:	mov    0xc8(%rdi),%rax
   131be:	jne    13172 <arx::x5::ControllerBase::CatchPositionCtrl()+0x82>
   131c0:	movsd  0x1f3f8(%rip),%xmm0        # 325c0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x38>
   131c8:	comisd %xmm1,%xmm0
   131cc:	ja     132a0 <arx::x5::ControllerBase::CatchPositionCtrl()+0x1b0>
   131d2:	movsd  0x1f3de(%rip),%xmm2        # 325b8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x30>
   131da:	movapd %xmm2,%xmm4
   131de:	minsd  %xmm1,%xmm4
   131e2:	movapd %xmm4,%xmm1
   131e6:	movsd  0xd8(%rdx),%xmm0
   131ee:	comisd 0x1f3da(%rip),%xmm0        # 325d0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x48>
   131f6:	movsd  %xmm1,0xc0(%rcx)
   131fe:	jbe    13260 <arx::x5::ControllerBase::CatchPositionCtrl()+0x170>
   13200:	mov    0x168(%rdi),%esi
   13206:	add    $0x1,%esi
   13209:	mov    %esi,0x168(%rdi)
   1320f:	cmp    $0x32,%esi
   13212:	jle    1326a <arx::x5::ControllerBase::CatchPositionCtrl()+0x17a>
   13214:	movsd  0xc0(%rdx),%xmm0
   1321c:	movapd %xmm1,%xmm3
   13220:	subsd  %xmm0,%xmm3
   13224:	comisd 0x1f36c(%rip),%xmm3        # 32598 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x10>
   1322c:	jbe    1326a <arx::x5::ControllerBase::CatchPositionCtrl()+0x17a>
   1322e:	movsd  0x1f3a2(%rip),%xmm1        # 325d8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x50>
   13236:	addsd  %xmm0,%xmm1
   1323a:	movsd  %xmm1,0xc0(%rcx)
   13242:	jmp    1326a <arx::x5::ControllerBase::CatchPositionCtrl()+0x17a>
   13244:	nopl   0x0(%rax)
   13248:	movaps %xmm2,%xmm0
   1324b:	jmp    13162 <arx::x5::ControllerBase::CatchPositionCtrl()+0x72>
   13250:	movsd  0x160(%rdi),%xmm0
   13258:	jmp    13144 <arx::x5::ControllerBase::CatchPositionCtrl()+0x54>
   1325d:	nopl   (%rax)
   13260:	movl   $0x0,0x168(%rdi)
   1326a:	mov    0x1f36f(%rip),%rsi        # 325e0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x58>
   13271:	movsd  %xmm2,0x110(%rax)
   13279:	movq   $0x0,0xf8(%rax)
   13284:	mov    %rsi,0x108(%rax)
   1328b:	movq   $0x0,0x100(%rax)
   13296:	movsd  %xmm1,0xf0(%rax)
   1329e:	ret
   1329f:	nop
   132a0:	movsd  0x1f310(%rip),%xmm2        # 325b8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x30>
   132a8:	movapd %xmm0,%xmm1
   132ac:	jmp    131e6 <arx::x5::ControllerBase::CatchPositionCtrl()+0xf6>
   132b1:	nop
   132b2:	data16 cs nopw 0x0(%rax,%rax,1)
   132bd:	nopl   (%rax)

00000000000132c0 <arx::x5::ControllerBase::statePositionControl()>:
   132c0:	endbr64
   132c4:	push   %r14
   132c6:	push   %r13
   132c8:	push   %r12
   132ca:	push   %rbp
   132cb:	mov    %rdi,%rbp
   132ce:	push   %rbx
   132cf:	sub    $0x70,%rsp
   132d3:	movsd  0x3b0(%rdi),%xmm0
   132db:	mov    %fs:0x28,%rax
   132e4:	mov    %rax,0x68(%rsp)
   132e9:	xor    %eax,%eax
   132eb:	mov    0xb0(%rdi),%rax
   132f2:	movsd  (%rax),%xmm1
   132f6:	comisd %xmm1,%xmm0
   132fa:	ja     13308 <arx::x5::ControllerBase::statePositionControl()+0x48>
   132fc:	movsd  0x3e8(%rdi),%xmm0
   13304:	minsd  %xmm1,%xmm0
   13308:	movsd  %xmm0,(%rsp)
   1330d:	movsd  0x3b8(%rbp),%xmm0
   13315:	movsd  0x20(%rax),%xmm1
   1331a:	comisd %xmm1,%xmm0
   1331e:	ja     1332c <arx::x5::ControllerBase::statePositionControl()+0x6c>
   13320:	movsd  0x3f0(%rbp),%xmm0
   13328:	minsd  %xmm1,%xmm0
   1332c:	movsd  0x40(%rax),%xmm1
   13331:	movsd  %xmm0,0x8(%rsp)
   13337:	movsd  0x3c0(%rbp),%xmm0
   1333f:	comisd %xmm1,%xmm0
   13343:	ja     13351 <arx::x5::ControllerBase::statePositionControl()+0x91>
   13345:	movsd  0x3f8(%rbp),%xmm0
   1334d:	minsd  %xmm1,%xmm0
   13351:	movsd  0x60(%rax),%xmm1
   13356:	movsd  %xmm0,0x10(%rsp)
   1335c:	movsd  0x3c8(%rbp),%xmm0
   13364:	comisd %xmm1,%xmm0
   13368:	ja     13376 <arx::x5::ControllerBase::statePositionControl()+0xb6>
   1336a:	movsd  0x400(%rbp),%xmm0
   13372:	minsd  %xmm1,%xmm0
   13376:	movsd  0x80(%rax),%xmm1
   1337e:	movsd  %xmm0,0x18(%rsp)
   13384:	movsd  0x3d0(%rbp),%xmm0
   1338c:	comisd %xmm1,%xmm0
   13390:	ja     1339e <arx::x5::ControllerBase::statePositionControl()+0xde>
   13392:	movsd  0x408(%rbp),%xmm0
   1339a:	minsd  %xmm1,%xmm0
   1339e:	movsd  0xa0(%rax),%xmm1
   133a6:	movsd  %xmm0,0x20(%rsp)
   133ac:	movsd  0x3d8(%rbp),%xmm0
   133b4:	comisd %xmm1,%xmm0
   133b8:	ja     133c6 <arx::x5::ControllerBase::statePositionControl()+0x106>
   133ba:	movsd  0x410(%rbp),%xmm0
   133c2:	minsd  %xmm1,%xmm0
   133c6:	movsd  %xmm0,0x28(%rsp)
   133cc:	xor    %ebx,%ebx
   133ce:	lea    0x30(%rsp),%r14
   133d3:	mov    %rsp,%r12
   133d6:	lea    0x78(%rbp),%r13
   133da:	nopw   0x0(%rax,%rax,1)
   133e0:	mov    0x1f1b9(%rip),%rax        # 325a0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x18>
   133e7:	movsd  0x178(%rbp),%xmm0
   133ef:	lea    (%r14,%rbx,1),%rdx
   133f3:	lea    0x0(%r13,%rbx,1),%rsi
   133f8:	movsd  0x180(%rbp),%xmm1
   13400:	lea    (%r12,%rbx,1),%rdi
   13404:	add    $0x8,%rbx
   13408:	movq   %rax,%xmm2
   1340d:	call   106f0 <arx::solve::Interpolation(double*, double*, double*, double, double, double)@plt>
   13412:	cmp    $0x30,%rbx
   13416:	jne    133e0 <arx::x5::ControllerBase::statePositionControl()+0x120>
   13418:	mov    0x4f8(%rbp),%rsi
   1341f:	mov    0xc8(%rbp),%rax
   13426:	mov    %rbp,%rdi
   13429:	mov    0x510(%rbp),%rcx
   13430:	mov    0x4b8(%rbp),%rdx
   13437:	movsd  (%rsi),%xmm0
   1343b:	movsd  %xmm0,0x18(%rax)
   13440:	movsd  (%rcx),%xmm0
   13444:	movsd  %xmm0,0x20(%rax)
   13449:	movsd  0x78(%rbp),%xmm0
   1344e:	movsd  %xmm0,(%rax)
   13452:	movsd  0x30(%rsp),%xmm0
   13458:	movsd  %xmm0,0x8(%rax)
   1345d:	movsd  (%rdx),%xmm0
   13461:	movsd  %xmm0,0x10(%rax)
   13466:	movsd  0x8(%rsi),%xmm0
   1346b:	movsd  %xmm0,0x40(%rax)
   13470:	movsd  0x8(%rcx),%xmm0
   13475:	movsd  %xmm0,0x48(%rax)
   1347a:	movsd  0x80(%rbp),%xmm0
   13482:	movsd  %xmm0,0x28(%rax)
   13487:	movsd  0x38(%rsp),%xmm0
   1348d:	movsd  %xmm0,0x30(%rax)
   13492:	movsd  0x8(%rdx),%xmm0
   13497:	movsd  %xmm0,0x38(%rax)
   1349c:	movsd  0x10(%rsi),%xmm0
   134a1:	movsd  %xmm0,0x68(%rax)
   134a6:	movsd  0x10(%rcx),%xmm0
   134ab:	movsd  %xmm0,0x70(%rax)
   134b0:	movsd  0x88(%rbp),%xmm0
   134b8:	movsd  %xmm0,0x50(%rax)
   134bd:	movsd  0x40(%rsp),%xmm0
   134c3:	movsd  %xmm0,0x58(%rax)
   134c8:	movsd  0x10(%rdx),%xmm0
   134cd:	movsd  %xmm0,0x60(%rax)
   134d2:	movsd  0x18(%rsi),%xmm0
   134d7:	movsd  %xmm0,0x90(%rax)
   134df:	movsd  0x18(%rcx),%xmm0
   134e4:	movsd  %xmm0,0x98(%rax)
   134ec:	movsd  0x90(%rbp),%xmm0
   134f4:	movsd  %xmm0,0x78(%rax)
   134f9:	movsd  0x48(%rsp),%xmm0
   134ff:	movsd  %xmm0,0x80(%rax)
   13507:	movsd  0x18(%rdx),%xmm0
   1350c:	movsd  %xmm0,0x88(%rax)
   13514:	movsd  0x20(%rsi),%xmm0
   13519:	movsd  %xmm0,0xb8(%rax)
   13521:	movsd  0x20(%rcx),%xmm0
   13526:	movsd  %xmm0,0xc0(%rax)
   1352e:	movsd  0x98(%rbp),%xmm0
   13536:	movsd  %xmm0,0xa0(%rax)
   1353e:	movsd  0x50(%rsp),%xmm0
   13544:	movsd  %xmm0,0xa8(%rax)
   1354c:	movsd  0x20(%rdx),%xmm0
   13551:	movsd  %xmm0,0xb0(%rax)
   13559:	movsd  0x28(%rsi),%xmm0
   1355e:	movsd  %xmm0,0xe0(%rax)
   13566:	movsd  0x28(%rcx),%xmm0
   1356b:	movsd  %xmm0,0xe8(%rax)
   13573:	movsd  0xa0(%rbp),%xmm0
   1357b:	movsd  %xmm0,0xc8(%rax)
   13583:	movsd  0x58(%rsp),%xmm0
   13589:	movsd  %xmm0,0xd0(%rax)
   13591:	movsd  0x28(%rdx),%xmm0
   13596:	movsd  %xmm0,0xd8(%rax)
   1359e:	call   10a30 <arx::x5::ControllerBase::CatchPositionCtrl()@plt>
   135a3:	mov    0x68(%rsp),%rax
   135a8:	xor    %fs:0x28,%rax
   135b1:	jne    135c0 <arx::x5::ControllerBase::statePositionControl()+0x300>
   135b3:	add    $0x70,%rsp
   135b7:	pop    %rbx
   135b8:	pop    %rbp
   135b9:	pop    %r12
   135bb:	pop    %r13
   135bd:	pop    %r14
   135bf:	ret
   135c0:	call   10ec0 <__stack_chk_fail@plt>
   135c5:	nop
   135c6:	cs nopw 0x0(%rax,%rax,1)

00000000000135d0 <arx::x5::ControllerBase::CatchSoft()>:
   135d0:	endbr64
   135d4:	mov    0xc8(%rdi),%rax
   135db:	pxor   %xmm0,%xmm0
   135df:	movq   $0x0,0x110(%rax)
   135ea:	movups %xmm0,0xf0(%rax)
   135f1:	movups %xmm0,0x100(%rax)
   135f8:	ret
   135f9:	nop
   135fa:	nopw   0x0(%rax,%rax,1)

0000000000013600 <arx::x5::ControllerBase::stateSoft()>:
   13600:	endbr64
   13604:	mov    0xc8(%rdi),%rax
   1360b:	pxor   %xmm0,%xmm0
   1360f:	movups %xmm0,0x20(%rax)
   13613:	movups %xmm0,0x40(%rax)
   13617:	movups %xmm0,0x60(%rax)
   1361b:	movups %xmm0,0x80(%rax)
   13622:	movups %xmm0,0xa0(%rax)
   13629:	movups %xmm0,(%rax)
   1362c:	movups %xmm0,0x10(%rax)
   13630:	movups %xmm0,0x30(%rax)
   13634:	movups %xmm0,0x50(%rax)
   13638:	movups %xmm0,0x70(%rax)
   1363c:	movups %xmm0,0x90(%rax)
   13643:	movups %xmm0,0xb0(%rax)
   1364a:	movups %xmm0,0xc0(%rax)
   13651:	movups %xmm0,0xd0(%rax)
   13658:	movups %xmm0,0xe0(%rax)
   1365f:	mov    0x188(%rdi),%rax
   13666:	movsd  (%rax),%xmm0
   1366a:	movsd  %xmm0,0x78(%rdi)
   1366f:	movsd  0x20(%rax),%xmm0
   13674:	movsd  %xmm0,0x80(%rdi)
   1367c:	movsd  0x40(%rax),%xmm0
   13681:	movsd  %xmm0,0x88(%rdi)
   13689:	movsd  0x60(%rax),%xmm0
   1368e:	movsd  %xmm0,0x90(%rdi)
   13696:	movsd  0x80(%rax),%xmm0
   1369e:	movsd  %xmm0,0x98(%rdi)
   136a6:	movsd  0xa0(%rax),%xmm0
   136ae:	movsd  %xmm0,0xa0(%rdi)
   136b6:	jmp    10590 <arx::x5::ControllerBase::CatchSoft()@plt>
   136bb:	nop
   136bc:	nopl   0x0(%rax)

00000000000136c0 <arx::x5::ControllerBase::stateProtect()>:
   136c0:	endbr64
   136c4:	mov    0x4e0(%rdi),%rdx
   136cb:	mov    0xc8(%rdi),%rax
   136d2:	movq   $0x0,0x18(%rax)
   136da:	movsd  (%rdx),%xmm0
   136de:	movq   $0x0,(%rax)
   136e5:	movq   $0x0,0x8(%rax)
   136ed:	movq   $0x0,0x10(%rax)
   136f5:	movq   $0x0,0x40(%rax)
   136fd:	movsd  %xmm0,0x20(%rax)
   13702:	movsd  0x8(%rdx),%xmm0
   13707:	movq   $0x0,0x28(%rax)
   1370f:	movq   $0x0,0x30(%rax)
   13717:	movq   $0x0,0x38(%rax)
   1371f:	movq   $0x0,0x68(%rax)
   13727:	movsd  %xmm0,0x48(%rax)
   1372c:	movsd  0x10(%rdx),%xmm0
   13731:	movq   $0x0,0x50(%rax)
   13739:	movq   $0x0,0x58(%rax)
   13741:	movq   $0x0,0x60(%rax)
   13749:	movq   $0x0,0x90(%rax)
   13754:	movsd  %xmm0,0x70(%rax)
   13759:	movsd  0x18(%rdx),%xmm0
   1375e:	movq   $0x0,0x78(%rax)
   13766:	movq   $0x0,0x80(%rax)
   13771:	movq   $0x0,0x88(%rax)
   1377c:	movq   $0x0,0xb8(%rax)
   13787:	movsd  %xmm0,0x98(%rax)
   1378f:	movsd  0x20(%rdx),%xmm0
   13794:	movq   $0x0,0xa0(%rax)
   1379f:	movsd  %xmm0,0xc0(%rax)
   137a7:	movq   $0x0,0xa8(%rax)
   137b2:	movq   $0x0,0xb0(%rax)
   137bd:	movq   $0x0,0xe0(%rax)
   137c8:	movsd  0x28(%rdx),%xmm0
   137cd:	movq   $0x0,0xc8(%rax)
   137d8:	movsd  %xmm0,0xe8(%rax)
   137e0:	movq   $0x0,0xd0(%rax)
   137eb:	movq   $0x0,0xd8(%rax)
   137f6:	mov    0x188(%rdi),%rax
   137fd:	movsd  (%rax),%xmm0
   13801:	movsd  %xmm0,0x78(%rdi)
   13806:	movsd  0x20(%rax),%xmm0
   1380b:	movsd  %xmm0,0x80(%rdi)
   13813:	movsd  0x40(%rax),%xmm0
   13818:	movsd  %xmm0,0x88(%rdi)
   13820:	movsd  0x60(%rax),%xmm0
   13825:	movsd  %xmm0,0x90(%rdi)
   1382d:	movsd  0x80(%rax),%xmm0
   13835:	movsd  %xmm0,0x98(%rdi)
   1383d:	movsd  0xa0(%rax),%xmm0
   13845:	movsd  %xmm0,0xa0(%rdi)
   1384d:	jmp    10590 <arx::x5::ControllerBase::CatchSoft()@plt>
   13852:	data16 cs nopw 0x0(%rax,%rax,1)
   1385d:	nopl   (%rax)

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

0000000000014620 <arx::x5::ControllerBase::update()>:
   14620:	endbr64
   14624:	push   %rbx
   14625:	mov    %rdi,%rbx
   14628:	sub    $0x20,%rsp
   1462c:	mov    %fs:0x28,%rax
   14635:	mov    %rax,0x18(%rsp)
   1463a:	xor    %eax,%eax
   1463c:	cmpb   $0x0,0x1(%rdi)
   14640:	je     146d0 <arx::x5::ControllerBase::update()+0xb0>
   14646:	cmpb   $0x0,0x2(%rdi)
   1464a:	je     14670 <arx::x5::ControllerBase::update()+0x50>
   1464c:	mov    0x10(%rdi),%eax
   1464f:	cmp    $0x5,%eax
   14652:	ja     14af0 <arx::x5::ControllerBase::update()+0x4d0>
   14658:	lea    0x1d9e1(%rip),%rdx        # 32040 <_fini+0x534>
   1465f:	movslq (%rdx,%rax,4),%rax
   14663:	add    %rdx,%rax
   14666:	notrack jmp *%rax
   14669:	nopl   0x0(%rax)
   14670:	call   10490 <arx::x5::ControllerBase::stateGoHome()@plt>
   14675:	cmpb   $0x0,0xc(%rbx)
   14679:	je     146f0 <arx::x5::ControllerBase::update()+0xd0>
   1467b:	mov    0xc8(%rbx),%rax
   14682:	mov    0x1df57(%rip),%rsi        # 325e0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x58>
   14689:	pxor   %xmm0,%xmm0
   1468d:	mov    %rsi,0x110(%rax)
   14694:	movups %xmm0,0xf0(%rax)
   1469b:	movups %xmm0,0x100(%rax)
   146a2:	cmpb   $0x0,(%rbx)
   146a5:	je     146b0 <arx::x5::ControllerBase::update()+0x90>
   146a7:	movb   $0x1,0x2(%rbx)
   146ab:	nopl   0x0(%rax,%rax,1)
   146b0:	mov    0x18(%rsp),%rax
   146b5:	xor    %fs:0x28,%rax
   146be:	jne    14c4f <arx::x5::ControllerBase::update()+0x62f>
   146c4:	add    $0x20,%rsp
   146c8:	pop    %rbx
   146c9:	ret
   146ca:	nopw   0x0(%rax,%rax,1)
   146d0:	call   11210 <arx::x5::ControllerBase::stateProtect()@plt>
   146d5:	mov    0x4(%rbx),%eax
   146d8:	add    $0x1,%eax
   146db:	mov    %eax,0x4(%rbx)
   146de:	cmp    $0x64,%eax
   146e1:	jne    146b0 <arx::x5::ControllerBase::update()+0x90>
   146e3:	movb   $0x1,0x1(%rbx)
   146e7:	jmp    146b0 <arx::x5::ControllerBase::update()+0x90>
   146e9:	nopl   0x0(%rax)
   146f0:	mov    0x8(%rbx),%eax
   146f3:	mov    0xc8(%rbx),%rdx
   146fa:	mov    0x1dea7(%rip),%rsi        # 325a8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x20>
   14701:	add    $0x1,%eax
   14704:	cmpl   $0x2,0x258(%rbx)
   1470b:	mov    %rsi,0x110(%rdx)
   14712:	je     14be0 <arx::x5::ControllerBase::update()+0x5c0>
   14718:	movapd 0x1df60(%rip),%xmm0        # 32680 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xf8>
   14720:	movups %xmm0,0xf0(%rdx)
   14727:	pxor   %xmm0,%xmm0
   1472b:	movups %xmm0,0x100(%rdx)
   14732:	mov    %eax,0x8(%rbx)
   14735:	cmp    $0x2bb,%eax
   1473a:	jle    146b0 <arx::x5::ControllerBase::update()+0x90>
   14740:	mov    0x188(%rbx),%rax
   14747:	movsd  0xc0(%rax),%xmm0
   1474f:	mov    0x18(%rbx),%rax
   14753:	movsd  %xmm0,0x30(%rax)
   14758:	movb   $0x1,0xc(%rbx)
   1475c:	jmp    146a2 <arx::x5::ControllerBase::update()+0x82>
   14761:	nopl   0x0(%rax)
   14768:	call   10a90 <arx::x5::ControllerBase::statePositionControl()@plt>
   1476d:	nopl   (%rax)
   14770:	mov    0xc8(%rbx),%rax
   14777:	pxor   %xmm0,%xmm0
   1477b:	mov    0x540(%rbx),%rdx
   14782:	movsd  0x18(%rax),%xmm1
   14787:	comisd %xmm0,%xmm1
   1478b:	jbe    14bd0 <arx::x5::ControllerBase::update()+0x5b0>
   14791:	mov    0x188(%rbx),%rcx
   14798:	movsd  (%rax),%xmm1
   1479c:	movsd  0x1de44(%rip),%xmm2        # 325e8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x60>
   147a4:	divsd  0x560(%rbx),%xmm2
   147ac:	subsd  (%rcx),%xmm1
   147b0:	mulsd  %xmm2,%xmm1
   147b4:	addsd  (%rdx),%xmm1
   147b8:	movsd  %xmm1,(%rdx)
   147bc:	movsd  0x558(%rbx),%xmm2
   147c4:	comisd %xmm2,%xmm1
   147c8:	ja     14b10 <arx::x5::ControllerBase::update()+0x4f0>
   147ce:	xorpd  0x1deba(%rip),%xmm2        # 32690 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x108>
   147d6:	comisd %xmm1,%xmm2
   147da:	ja     14b10 <arx::x5::ControllerBase::update()+0x4f0>
   147e0:	movapd %xmm1,%xmm2
   147e4:	mov    0x528(%rbx),%rcx
   147eb:	mulsd  (%rcx),%xmm2
   147ef:	addsd  0x10(%rax),%xmm2
   147f4:	movsd  %xmm2,0x10(%rax)
   147f9:	movsd  0x40(%rax),%xmm1
   147fe:	comisd %xmm0,%xmm1
   14802:	jbe    14bc0 <arx::x5::ControllerBase::update()+0x5a0>
   14808:	mov    0x188(%rbx),%rcx
   1480f:	movsd  0x28(%rax),%xmm1
   14814:	movsd  0x1ddcc(%rip),%xmm2        # 325e8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x60>
   1481c:	divsd  0x560(%rbx),%xmm2
   14824:	subsd  0x20(%rcx),%xmm1
   14829:	mulsd  %xmm2,%xmm1
   1482d:	addsd  0x8(%rdx),%xmm1
   14832:	movsd  %xmm1,0x8(%rdx)
   14837:	movsd  0x558(%rbx),%xmm2
   1483f:	comisd %xmm2,%xmm1
   14843:	ja     14b00 <arx::x5::ControllerBase::update()+0x4e0>
   14849:	xorpd  0x1de3f(%rip),%xmm2        # 32690 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x108>
   14851:	comisd %xmm1,%xmm2
   14855:	ja     14b00 <arx::x5::ControllerBase::update()+0x4e0>
   1485b:	movapd %xmm1,%xmm2
   1485f:	mov    0x528(%rbx),%rcx
   14866:	mulsd  0x8(%rcx),%xmm2
   1486b:	addsd  0x38(%rax),%xmm2
   14870:	movsd  %xmm2,0x38(%rax)
   14875:	movsd  0x68(%rax),%xmm1
   1487a:	comisd %xmm0,%xmm1
   1487e:	jbe    14b60 <arx::x5::ControllerBase::update()+0x540>
   14884:	mov    0x188(%rbx),%rcx
   1488b:	movsd  0x50(%rax),%xmm1
   14890:	movsd  0x1dd50(%rip),%xmm2        # 325e8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x60>
   14898:	divsd  0x560(%rbx),%xmm2
   148a0:	subsd  0x40(%rcx),%xmm1
   148a5:	mulsd  %xmm2,%xmm1
   148a9:	addsd  0x10(%rdx),%xmm1
   148ae:	movsd  %xmm1,0x10(%rdx)
   148b3:	movsd  0x558(%rbx),%xmm2
   148bb:	comisd %xmm2,%xmm1
   148bf:	ja     14b50 <arx::x5::ControllerBase::update()+0x530>
   148c5:	xorpd  0x1ddc3(%rip),%xmm2        # 32690 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x108>
   148cd:	comisd %xmm1,%xmm2
   148d1:	ja     14b50 <arx::x5::ControllerBase::update()+0x530>
   148d7:	movapd %xmm1,%xmm2
   148db:	mov    0x528(%rbx),%rcx
   148e2:	movsd  0x90(%rax),%xmm1
   148ea:	mulsd  0x10(%rcx),%xmm2
   148ef:	comisd %xmm0,%xmm1
   148f3:	addsd  0x60(%rax),%xmm2
   148f8:	movsd  %xmm2,0x60(%rax)
   148fd:	jbe    14b7a <arx::x5::ControllerBase::update()+0x55a>
   14903:	mov    0x188(%rbx),%rcx
   1490a:	movsd  0x78(%rax),%xmm1
   1490f:	movsd  0x1dcd1(%rip),%xmm2        # 325e8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x60>
   14917:	divsd  0x560(%rbx),%xmm2
   1491f:	subsd  0x60(%rcx),%xmm1
   14924:	mulsd  %xmm2,%xmm1
   14928:	addsd  0x18(%rdx),%xmm1
   1492d:	movsd  %xmm1,0x18(%rdx)
   14932:	movsd  0x558(%rbx),%xmm2
   1493a:	comisd %xmm2,%xmm1
   1493e:	ja     14b40 <arx::x5::ControllerBase::update()+0x520>
   14944:	xorpd  0x1dd44(%rip),%xmm2        # 32690 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x108>
   1494c:	comisd %xmm1,%xmm2
   14950:	ja     14b40 <arx::x5::ControllerBase::update()+0x520>
   14956:	movapd %xmm1,%xmm2
   1495a:	mov    0x528(%rbx),%rcx
   14961:	movsd  0xb8(%rax),%xmm1
   14969:	mulsd  0x18(%rcx),%xmm2
   1496e:	comisd %xmm0,%xmm1
   14972:	addsd  0x88(%rax),%xmm2
   1497a:	movsd  %xmm2,0x88(%rax)
   14982:	jbe    14b94 <arx::x5::ControllerBase::update()+0x574>
   14988:	mov    0x188(%rbx),%rcx
   1498f:	movsd  0xa0(%rax),%xmm1
   14997:	movsd  0x1dc49(%rip),%xmm2        # 325e8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x60>
   1499f:	divsd  0x560(%rbx),%xmm2
   149a7:	subsd  0x80(%rcx),%xmm1
   149af:	mulsd  %xmm2,%xmm1
   149b3:	addsd  0x20(%rdx),%xmm1
   149b8:	movsd  %xmm1,0x20(%rdx)
   149bd:	movsd  0x558(%rbx),%xmm2
   149c5:	comisd %xmm2,%xmm1
   149c9:	ja     14b30 <arx::x5::ControllerBase::update()+0x510>
   149cf:	xorpd  0x1dcb9(%rip),%xmm2        # 32690 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x108>
   149d7:	comisd %xmm1,%xmm2
   149db:	ja     14b30 <arx::x5::ControllerBase::update()+0x510>
   149e1:	movapd %xmm1,%xmm2
   149e5:	mov    0x528(%rbx),%rcx
   149ec:	movsd  0xe0(%rax),%xmm1
   149f4:	mulsd  0x20(%rcx),%xmm2
   149f9:	comisd %xmm0,%xmm1
   149fd:	addsd  0xb0(%rax),%xmm2
   14a05:	movsd  %xmm2,0xb0(%rax)
   14a0d:	jbe    14bae <arx::x5::ControllerBase::update()+0x58e>
   14a13:	mov    0x188(%rbx),%rcx
   14a1a:	movsd  0xc8(%rax),%xmm0
   14a22:	movsd  0x1dbbe(%rip),%xmm1        # 325e8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x60>
   14a2a:	divsd  0x560(%rbx),%xmm1
   14a32:	subsd  0xa0(%rcx),%xmm0
   14a3a:	mulsd  %xmm1,%xmm0
   14a3e:	addsd  0x28(%rdx),%xmm0
   14a43:	movsd  %xmm0,0x28(%rdx)
   14a48:	movsd  0x558(%rbx),%xmm1
   14a50:	comisd %xmm1,%xmm0
   14a54:	ja     14b20 <arx::x5::ControllerBase::update()+0x500>
   14a5a:	xorpd  0x1dc2e(%rip),%xmm1        # 32690 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x108>
   14a62:	comisd %xmm0,%xmm1
   14a66:	ja     14b20 <arx::x5::ControllerBase::update()+0x500>
   14a6c:	movapd %xmm0,%xmm1
   14a70:	mov    0x528(%rbx),%rdx
   14a77:	mulsd  0x28(%rdx),%xmm1
   14a7c:	addsd  0xd8(%rax),%xmm1
   14a84:	movsd  %xmm1,0xd8(%rax)
   14a8c:	jmp    146b0 <arx::x5::ControllerBase::update()+0x90>
   14a91:	nopl   0x0(%rax)
   14a98:	call   10c90 <arx::x5::ControllerBase::stateEndControl()@plt>
   14a9d:	jmp    14770 <arx::x5::ControllerBase::update()+0x150>
   14aa2:	nopw   0x0(%rax,%rax,1)
   14aa8:	call   10e90 <arx::x5::ControllerBase::stateGravityCompensation()@plt>
   14aad:	jmp    14770 <arx::x5::ControllerBase::update()+0x150>
   14ab2:	nopw   0x0(%rax,%rax,1)
   14ab8:	call   10490 <arx::x5::ControllerBase::stateGoHome()@plt>
   14abd:	mov    0xb0(%rbx),%rax
   14ac4:	mov    %rbx,%rdi
   14ac7:	movq   $0x0,0xc0(%rax)
   14ad2:	call   10a30 <arx::x5::ControllerBase::CatchPositionCtrl()@plt>
   14ad7:	jmp    14770 <arx::x5::ControllerBase::update()+0x150>
   14adc:	nopl   0x0(%rax)
   14ae0:	call   116d0 <arx::x5::ControllerBase::stateSoft()@plt>
   14ae5:	jmp    14770 <arx::x5::ControllerBase::update()+0x150>
   14aea:	nopw   0x0(%rax,%rax,1)
   14af0:	call   11210 <arx::x5::ControllerBase::stateProtect()@plt>
   14af5:	jmp    14770 <arx::x5::ControllerBase::update()+0x150>
   14afa:	nopw   0x0(%rax,%rax,1)
   14b00:	movsd  %xmm2,0x8(%rdx)
   14b05:	jmp    1485f <arx::x5::ControllerBase::update()+0x23f>
   14b0a:	nopw   0x0(%rax,%rax,1)
   14b10:	movsd  %xmm2,(%rdx)
   14b14:	jmp    147e4 <arx::x5::ControllerBase::update()+0x1c4>
   14b19:	nopl   0x0(%rax)
   14b20:	movsd  %xmm1,0x28(%rdx)
   14b25:	jmp    14a70 <arx::x5::ControllerBase::update()+0x450>
   14b2a:	nopw   0x0(%rax,%rax,1)
   14b30:	movsd  %xmm2,0x20(%rdx)
   14b35:	jmp    149e5 <arx::x5::ControllerBase::update()+0x3c5>
   14b3a:	nopw   0x0(%rax,%rax,1)
   14b40:	movsd  %xmm2,0x18(%rdx)
   14b45:	jmp    1495a <arx::x5::ControllerBase::update()+0x33a>
   14b4a:	nopw   0x0(%rax,%rax,1)
   14b50:	movsd  %xmm2,0x10(%rdx)
   14b55:	jmp    148db <arx::x5::ControllerBase::update()+0x2bb>
   14b5a:	nopw   0x0(%rax,%rax,1)
   14b60:	movq   $0x0,0x10(%rdx)
   14b68:	movsd  0x90(%rax),%xmm1
   14b70:	comisd %xmm0,%xmm1
   14b74:	ja     14903 <arx::x5::ControllerBase::update()+0x2e3>
   14b7a:	movq   $0x0,0x18(%rdx)
   14b82:	movsd  0xb8(%rax),%xmm1
   14b8a:	comisd %xmm0,%xmm1
   14b8e:	ja     14988 <arx::x5::ControllerBase::update()+0x368>
   14b94:	movq   $0x0,0x20(%rdx)
   14b9c:	movsd  0xe0(%rax),%xmm1
   14ba4:	comisd %xmm0,%xmm1
   14ba8:	ja     14a13 <arx::x5::ControllerBase::update()+0x3f3>
   14bae:	movq   $0x0,0x28(%rdx)
   14bb6:	jmp    146b0 <arx::x5::ControllerBase::update()+0x90>
   14bbb:	nopl   0x0(%rax,%rax,1)
   14bc0:	movq   $0x0,0x8(%rdx)
   14bc8:	jmp    14875 <arx::x5::ControllerBase::update()+0x255>
   14bcd:	nopl   (%rax)
   14bd0:	movq   $0x0,(%rdx)
   14bd7:	jmp    147f9 <arx::x5::ControllerBase::update()+0x1d9>
   14bdc:	nopl   0x0(%rax)
   14be0:	movapd 0x1da88(%rip),%xmm0        # 32670 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xe8>
   14be8:	movups %xmm0,0xf0(%rdx)
   14bef:	pxor   %xmm0,%xmm0
   14bf3:	movups %xmm0,0x100(%rdx)
   14bfa:	mov    %eax,0x8(%rbx)
   14bfd:	cmp    $0x2bb,%eax
   14c02:	jle    146b0 <arx::x5::ControllerBase::update()+0x90>
   14c08:	mov    0x188(%rbx),%rax
   14c0f:	movsd  0xc0(%rax),%xmm0
   14c17:	mov    0x18(%rbx),%rax
   14c1b:	movsd  %xmm0,0x30(%rax)
   14c20:	mov    0x428(%rbx),%rax
   14c27:	mov    0x60(%rax),%rdi
   14c2b:	mov    (%rdi),%rax
   14c2e:	call   *0x40(%rax)
   14c31:	mov    0x420(%rbx),%rdi
   14c38:	mov    %rsp,%rsi
   14c3b:	mov    %rax,(%rsp)
   14c3f:	mov    %rdx,0x8(%rsp)
   14c44:	mov    (%rdi),%rax
   14c47:	call   *0x8(%rax)
   14c4a:	jmp    14758 <arx::x5::ControllerBase::update()+0x138>
   14c4f:	call   10ec0 <__stack_chk_fail@plt>
   14c54:	data16 cs nopw 0x0(%rax,%rax,1)
   14c5f:	nop

0000000000014c60 <arx::x5::ControllerBase::ifTorqeLimit()>:
   14c60:	endbr64
   14c64:	mov    0x188(%rdi),%rdx
   14c6b:	mov    0x30(%rdi),%rax
   14c6f:	xor    %ecx,%ecx
   14c71:	movq   0x1d9c7(%rip),%xmm0        # 32640 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xb8>
   14c79:	movsd  0x18(%rdx),%xmm1
   14c7e:	andpd  %xmm0,%xmm1
   14c82:	comisd (%rax),%xmm1
   14c86:	jbe    14c91 <arx::x5::ControllerBase::ifTorqeLimit()+0x31>
   14c88:	mov    0x25c(%rdi),%esi
   14c8e:	lea    0x1(%rsi),%ecx
   14c91:	movsd  0x38(%rdx),%xmm1
   14c96:	mov    %ecx,0x25c(%rdi)
   14c9c:	xor    %ecx,%ecx
   14c9e:	andpd  %xmm0,%xmm1
   14ca2:	comisd 0x8(%rax),%xmm1
   14ca7:	jbe    14cb2 <arx::x5::ControllerBase::ifTorqeLimit()+0x52>
   14ca9:	mov    0x260(%rdi),%esi
   14caf:	lea    0x1(%rsi),%ecx
   14cb2:	movsd  0x58(%rdx),%xmm1
   14cb7:	mov    %ecx,0x260(%rdi)
   14cbd:	xor    %esi,%esi
   14cbf:	andpd  %xmm0,%xmm1
   14cc3:	comisd 0x10(%rax),%xmm1
   14cc8:	jbe    14cd3 <arx::x5::ControllerBase::ifTorqeLimit()+0x73>
   14cca:	mov    0x264(%rdi),%esi
   14cd0:	add    $0x1,%esi
   14cd3:	movsd  0x78(%rdx),%xmm1
   14cd8:	mov    %esi,0x264(%rdi)
   14cde:	xor    %r8d,%r8d
   14ce1:	andpd  %xmm0,%xmm1
   14ce5:	comisd 0x18(%rax),%xmm1
   14cea:	jbe    14cf7 <arx::x5::ControllerBase::ifTorqeLimit()+0x97>
   14cec:	mov    0x268(%rdi),%r10d
   14cf3:	lea    0x1(%r10),%r8d
   14cf7:	movsd  0x98(%rdx),%xmm1
   14cff:	mov    %r8d,0x268(%rdi)
   14d06:	xor    %r9d,%r9d
   14d09:	andpd  %xmm0,%xmm1
   14d0d:	comisd 0x20(%rax),%xmm1
   14d12:	jbe    14d1f <arx::x5::ControllerBase::ifTorqeLimit()+0xbf>
   14d14:	mov    0x26c(%rdi),%r11d
   14d1b:	lea    0x1(%r11),%r9d
   14d1f:	movsd  0xb8(%rdx),%xmm1
   14d27:	mov    %r9d,0x26c(%rdi)
   14d2e:	xor    %edx,%edx
   14d30:	andpd  %xmm1,%xmm0
   14d34:	comisd 0x28(%rax),%xmm0
   14d39:	jbe    14d44 <arx::x5::ControllerBase::ifTorqeLimit()+0xe4>
   14d3b:	mov    0x270(%rdi),%eax
   14d41:	lea    0x1(%rax),%edx
   14d44:	mov    %edx,0x270(%rdi)
   14d4a:	mov    0x278(%rdi),%eax
   14d50:	cmp    0x25c(%rdi),%eax
   14d56:	jle    14d70 <arx::x5::ControllerBase::ifTorqeLimit()+0x110>
   14d58:	cmp    %ecx,%eax
   14d5a:	jle    14d70 <arx::x5::ControllerBase::ifTorqeLimit()+0x110>
   14d5c:	cmp    %esi,%eax
   14d5e:	jle    14d70 <arx::x5::ControllerBase::ifTorqeLimit()+0x110>
   14d60:	cmp    %r8d,%eax
   14d63:	jle    14d70 <arx::x5::ControllerBase::ifTorqeLimit()+0x110>
   14d65:	cmp    %r9d,%eax
   14d68:	jle    14d70 <arx::x5::ControllerBase::ifTorqeLimit()+0x110>
   14d6a:	cmp    %edx,%eax
   14d6c:	setg   %al
   14d6f:	ret
   14d70:	xor    %eax,%eax
   14d72:	ret
   14d73:	nop
   14d74:	data16 cs nopw 0x0(%rax,%rax,1)
   14d7f:	nop

00000000000158d0 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)>:
   158d0:	endbr64
   158d4:	push   %r15
   158d6:	pxor   %xmm0,%xmm0
   158da:	push   %r14
   158dc:	push   %r13
   158de:	mov    %ecx,%r13d
   158e1:	push   %r12
   158e3:	mov    %rdx,%r12
   158e6:	push   %rbp
   158e7:	push   %rbx
   158e8:	mov    %rdi,%rbx
   158eb:	sub    $0x178,%rsp
   158f2:	mov    %rsi,(%rsp)
   158f6:	mov    %fs:0x28,%rax
   158ff:	mov    %rax,0x168(%rsp)
   15907:	xor    %eax,%eax
   15909:	xor    %eax,%eax
   1590b:	movb   $0x0,0x2(%rdi)
   1590f:	mov    %ax,(%rdi)
   15912:	movq   $0x0,0x4(%rdi)
   1591a:	movb   $0x0,0xc(%rdi)
   1591e:	movq   $0x0,0x28(%rdi)
   15926:	movaps %xmm0,0xb0(%rsp)
   1592e:	movaps %xmm0,0xc0(%rsp)
   15936:	movaps %xmm0,0xd0(%rsp)
   1593e:	pxor   %xmm0,%xmm0
   15942:	movups %xmm0,0x18(%rdi)
   15946:	mov    $0x38,%edi
   1594b:	movq   $0x0,0xe0(%rsp)
   15957:	call   10e00 <operator new(unsigned long)@plt>
   1595c:	mov    0xe0(%rsp),%rcx
   15964:	lea    0x38(%rax),%rdx
   15968:	movdqa 0xb0(%rsp),%xmm4
   15971:	mov    %rax,0x18(%rbx)
   15975:	mov    %rdx,0x28(%rbx)
   15979:	pxor   %xmm0,%xmm0
   1597d:	mov    $0x38,%edi
   15982:	movdqa 0xc0(%rsp),%xmm5
   1598b:	movdqa 0xd0(%rsp),%xmm6
   15994:	mov    %rcx,0x30(%rax)
   15998:	mov    %rdx,0x20(%rbx)
   1599c:	movq   $0x0,0x40(%rbx)
   159a4:	movups %xmm4,(%rax)
   159a7:	movups %xmm5,0x10(%rax)
   159ab:	movups %xmm6,0x20(%rax)
   159af:	movups %xmm0,0x30(%rbx)
   159b3:	call   10e00 <operator new(unsigned long)@plt>
   159b8:	movdqa 0x1c820(%rip),%xmm7        # 321e0 <C.0.322575>
   159c0:	lea    0x38(%rax),%rdx
   159c4:	mov    %rax,0x30(%rbx)
   159c8:	pxor   %xmm0,%xmm0
   159cc:	mov    0x1c83d(%rip),%rcx        # 32210 <C.0.322575+0x30>
   159d3:	movdqa 0x1c825(%rip),%xmm4        # 32200 <C.0.322575+0x20>
   159db:	mov    %rdx,0x40(%rbx)
   159df:	mov    $0x30,%edi
   159e4:	movups %xmm7,(%rax)
   159e7:	movdqa 0x1c801(%rip),%xmm7        # 321f0 <C.0.322575+0x10>
   159ef:	mov    %rcx,0x30(%rax)
   159f3:	mov    %rdx,0x38(%rbx)
   159f7:	movq   $0x0,0x58(%rbx)
   159ff:	movups %xmm7,0x10(%rax)
   15a03:	movups %xmm4,0x20(%rax)
   15a07:	movups %xmm0,0x48(%rbx)
   15a0b:	call   10e00 <operator new(unsigned long)@plt>
   15a10:	lea    0x30(%rax),%rdx
   15a14:	mov    %rax,0x48(%rbx)
   15a18:	pxor   %xmm0,%xmm0
   15a1c:	movdqa 0x1c77c(%rip),%xmm5        # 321a0 <C.1.322579>
   15a24:	movdqa 0x1c784(%rip),%xmm6        # 321b0 <C.1.322579+0x10>
   15a2c:	movdqa 0x1c78c(%rip),%xmm1        # 321c0 <C.1.322579+0x20>
   15a34:	mov    %rdx,0x58(%rbx)
   15a38:	mov    $0x30,%edi
   15a3d:	mov    %rdx,0x50(%rbx)
   15a41:	movq   $0x0,0x70(%rbx)
   15a49:	movups %xmm5,(%rax)
   15a4c:	movups %xmm6,0x10(%rax)
   15a50:	movups %xmm1,0x20(%rax)
   15a54:	movups %xmm0,0x60(%rbx)
   15a58:	call   10e00 <operator new(unsigned long)@plt>
   15a5d:	lea    0x30(%rax),%rdx
   15a61:	pxor   %xmm0,%xmm0
   15a65:	movdqa 0x1c6f3(%rip),%xmm2        # 32160 <C.2.322583>
   15a6d:	movdqa 0x1c6fb(%rip),%xmm7        # 32170 <C.2.322583+0x10>
   15a75:	movdqa 0x1c703(%rip),%xmm4        # 32180 <C.2.322583+0x20>
   15a7d:	mov    %rax,0x60(%rbx)
   15a81:	mov    $0xe0,%edi
   15a86:	mov    %rdx,0x70(%rbx)
   15a8a:	mov    %rdx,0x68(%rbx)
   15a8e:	movq   $0x0,0xa8(%rbx)
   15a99:	movq   $0x0,0xc0(%rbx)
   15aa4:	movups %xmm0,0x78(%rbx)
   15aa8:	movups %xmm0,0x88(%rbx)
   15aaf:	movups %xmm0,0x98(%rbx)
   15ab6:	pxor   %xmm0,%xmm0
   15aba:	movups %xmm2,(%rax)
   15abd:	movups %xmm7,0x10(%rax)
   15ac1:	movups %xmm4,0x20(%rax)
   15ac5:	movups %xmm0,0xb0(%rbx)
   15acc:	call   10e00 <operator new(unsigned long)@plt>
   15ad1:	lea    0xe0(%rax),%rdx
   15ad8:	pxor   %xmm0,%xmm0
   15adc:	mov    %rax,0xb0(%rbx)
   15ae3:	mov    $0x118,%edi
   15ae8:	mov    %rdx,0xc0(%rbx)
   15aef:	mov    %rdx,0xb8(%rbx)
   15af6:	movq   $0x0,0xc8(%rbx)
   15b01:	movups %xmm0,(%rax)
   15b04:	movups %xmm0,0x10(%rax)
   15b08:	movups %xmm0,0x20(%rax)
   15b0c:	movups %xmm0,0x30(%rax)
   15b10:	movups %xmm0,0x40(%rax)
   15b14:	movups %xmm0,0x50(%rax)
   15b18:	movups %xmm0,0x60(%rax)
   15b1c:	movups %xmm0,0x70(%rax)
   15b20:	movups %xmm0,0x80(%rax)
   15b27:	movups %xmm0,0x90(%rax)
   15b2e:	movups %xmm0,0xa0(%rax)
   15b35:	movups %xmm0,0xb0(%rax)
   15b3c:	movups %xmm0,0xc0(%rax)
   15b43:	movups %xmm0,0xd0(%rax)
   15b4a:	pxor   %xmm0,%xmm0
   15b4e:	movups %xmm0,0xd0(%rbx)
   15b55:	call   10e00 <operator new(unsigned long)@plt>
   15b5a:	pxor   %xmm0,%xmm0
   15b5e:	mov    $0xe0,%edi
   15b63:	lea    0x118(%rax),%rdx
   15b6a:	mov    %rax,0xc8(%rbx)
   15b71:	movups %xmm0,(%rax)
   15b74:	movups %xmm0,0x10(%rax)
   15b78:	movups %xmm0,0x20(%rax)
   15b7c:	movups %xmm0,0x30(%rax)
   15b80:	movups %xmm0,0x40(%rax)
   15b84:	movups %xmm0,0x50(%rax)
   15b88:	movups %xmm0,0x60(%rax)
   15b8c:	movups %xmm0,0x70(%rax)
   15b90:	movups %xmm0,0x80(%rax)
   15b97:	movups %xmm0,0x90(%rax)
   15b9e:	movups %xmm0,0xa0(%rax)
   15ba5:	movups %xmm0,0xb0(%rax)
   15bac:	movups %xmm0,0xc0(%rax)
   15bb3:	movups %xmm0,0xd0(%rax)
   15bba:	movups %xmm0,0xe0(%rax)
   15bc1:	movups %xmm0,0xf0(%rax)
   15bc8:	movups %xmm0,0x100(%rax)
   15bcf:	movapd 0x1cac9(%rip),%xmm0        # 326a0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x118>
   15bd7:	movq   $0x0,0x110(%rax)
   15be2:	mov    0x1c9ff(%rip),%rax        # 325e8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x60>
   15be9:	mov    %rdx,0xd8(%rbx)
   15bf0:	mov    %rdx,0xd0(%rbx)
   15bf7:	movq   $0x0,0xf8(%rbx)
   15c02:	movq   $0x0,0x118(%rbx)
   15c0d:	movq   $0x0,0x138(%rbx)
   15c18:	mov    %rax,0x158(%rbx)
   15c1f:	movl   $0x0,0x168(%rbx)
   15c29:	movb   $0x0,0x16c(%rbx)
   15c30:	movq   $0x0,0x198(%rbx)
   15c3b:	movups %xmm0,0x178(%rbx)
   15c42:	pxor   %xmm0,%xmm0
   15c46:	movups %xmm0,0x188(%rbx)
   15c4d:	call   10e00 <operator new(unsigned long)@plt>
   15c52:	pxor   %xmm0,%xmm0
   15c56:	lea    0x248(%rbx),%rbp
   15c5d:	lea    0xe0(%rax),%rdx
   15c64:	mov    %rax,0x188(%rbx)
   15c6b:	mov    %rbp,0x238(%rbx)
   15c72:	mov    (%r12),%r14
   15c76:	movups %xmm0,(%rax)
   15c79:	mov    0x8(%r12),%r12
   15c7e:	movups %xmm0,0x10(%rax)
   15c82:	movups %xmm0,0x20(%rax)
   15c86:	movups %xmm0,0x30(%rax)
   15c8a:	movups %xmm0,0x40(%rax)
   15c8e:	movups %xmm0,0x50(%rax)
   15c92:	movups %xmm0,0x60(%rax)
   15c96:	movups %xmm0,0x70(%rax)
   15c9a:	movups %xmm0,0x80(%rax)
   15ca1:	movups %xmm0,0x90(%rax)
   15ca8:	movups %xmm0,0xa0(%rax)
   15caf:	movups %xmm0,0xb0(%rax)
   15cb6:	movups %xmm0,0xc0(%rax)
   15cbd:	movups %xmm0,0xd0(%rax)
   15cc4:	mov    0x1c91d(%rip),%rax        # 325e8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x60>
   15ccb:	mov    %rdx,0x198(%rbx)
   15cd2:	mov    %rax,0x228(%rbx)
   15cd9:	mov    %r14,%rax
   15cdc:	add    %r12,%rax
   15cdf:	mov    %rdx,0x190(%rbx)
   15ce6:	movb   $0x1,0x1a0(%rbx)
   15ced:	movq   $0x0,0x1c8(%rbx)
   15cf8:	movq   $0x0,0x1e8(%rbx)
   15d03:	movq   $0x0,0x208(%rbx)
   15d0e:	movb   $0x0,0x230(%rbx)
   15d15:	je     15d20 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0x450>
   15d17:	test   %r14,%r14
   15d1a:	je     16b5f <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0x128f>
   15d20:	mov    %r12,0x78(%rsp)
   15d25:	cmp    $0xf,%r12
   15d29:	ja     169f0 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0x1120>
   15d2f:	cmp    $0x1,%r12
   15d33:	jne    167e0 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xf10>
   15d39:	movzbl (%r14),%eax
   15d3d:	mov    %al,0x248(%rbx)
   15d43:	mov    %rbp,%rax
   15d46:	mov    %r12,0x240(%rbx)
   15d4d:	pxor   %xmm0,%xmm0
   15d51:	mov    (%rsp),%rsi
   15d55:	lea    0x298(%rbx),%r15
   15d5c:	movb   $0x0,(%rax,%r12,1)
   15d61:	lea    0xf0(%rsp),%r12
   15d69:	lea    0x90(%rsp),%r14
   15d71:	mov    %r15,%rdi
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
   15e14:	mov    0x80(%rsp),%rdi
   15e1c:	cmp    %r14,%rdi
   15e1f:	je     15e26 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0x556>
   15e21:	call   10d80 <operator delete(void*)@plt>
   15e26:	mov    0xf0(%rsp),%rdi
   15e2e:	cmp    %r13,%rdi
   15e31:	je     15e38 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0x568>
   15e33:	call   10d80 <operator delete(void*)@plt>
   15e38:	movapd 0x1c870(%rip),%xmm0        # 326b0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x128>
   15e40:	mov    $0xb8,%edi
   15e45:	movq   $0x0,0x420(%rbx)
   15e50:	movaps %xmm0,0x3b0(%rbx)
   15e57:	movapd 0x1c861(%rip),%xmm0        # 326c0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x138>
   15e5f:	movaps %xmm0,0x3c0(%rbx)
   15e66:	movapd 0x1c862(%rip),%xmm0        # 326d0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x148>
   15e6e:	movaps %xmm0,0x3d0(%rbx)
   15e75:	movapd 0x1c863(%rip),%xmm0        # 326e0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x158>
   15e7d:	movaps %xmm0,0x3e0(%rbx)
   15e84:	movapd 0x1c864(%rip),%xmm0        # 326f0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x168>
   15e8c:	movaps %xmm0,0x3f0(%rbx)
   15e93:	movapd 0x1c865(%rip),%xmm0        # 32700 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x178>
   15e9b:	movaps %xmm0,0x400(%rbx)
   15ea2:	movapd 0x1c866(%rip),%xmm0        # 32710 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x188>
   15eaa:	movaps %xmm0,0x410(%rbx)
   15eb1:	call   10e00 <operator new(unsigned long)@plt>
   15eb6:	mov    0x2604b(%rip),%r14        # 3bf08 <vtable for std::_Sp_counted_ptr_inplace<arx::hw_interface::MotorType4, std::allocator<arx::hw_interface::MotorType4>, (__gnu_cxx::_Lock_policy)2>@@Base+0x558>
   15ebd:	mov    %rax,%rdx
   15ec0:	mov    0x26109(%rip),%r13        # 3bfd0 <vtable for arx::hw_interface::MotorType4@@Base+0x488>
   15ec7:	movabs $0x100000001,%rax
   15ed1:	mov    %rax,0x8(%rdx)
   15ed5:	pxor   %xmm0,%xmm0
   15ed9:	lea    0x10(%rdx),%rsi
   15edd:	mov    0x1c714(%rip),%rcx        # 325f8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x70>
   15ee4:	lea    0x10(%r14),%rax
   15ee8:	movb   $0x1,0x38(%rdx)
   15eec:	movapd 0x1c82c(%rip),%xmm5        # 32720 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x198>
   15ef4:	mov    %rax,(%rdx)
   15ef7:	lea    0x10(%r13),%rax
   15efb:	movl   $0x0,0x18(%rdx)
   15f02:	mov    %rax,0x10(%rdx)
   15f06:	movq   $0x0,0x30(%rdx)
   15f0e:	movq   $0x0,0x40(%rdx)
   15f16:	movl   $0x0,0x58(%rdx)
   15f1d:	movl   $0x0,0x70(%rdx)
   15f24:	movq   $0x0,0x80(%rdx)
   15f2f:	movl   $0x0,0x88(%rdx)
   15f39:	mov    %rcx,0xa0(%rdx)
   15f40:	movl   $0x1,0xb0(%rdx)
   15f4a:	movups %xmm0,0x20(%rdx)
   15f4e:	movups %xmm0,0x48(%rdx)
   15f52:	movups %xmm0,0x60(%rdx)
   15f56:	movups %xmm5,0x90(%rdx)
   15f5d:	mov    %rsi,(%rsp)
   15f61:	mov    %rdx,0x10(%rsp)
   15f66:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   15f6b:	mov    (%rsp),%rsi
   15f6f:	mov    0x10(%rsp),%rdx
   15f74:	mov    $0xb8,%edi
   15f79:	mov    %rax,0x70(%rsi)
   15f7d:	movq   %rsi,%xmm3
   15f82:	movq   %rdx,%xmm6
   15f87:	punpcklqdq %xmm6,%xmm3
   15f8b:	movaps %xmm3,0x30(%rsp)
   15f90:	movaps %xmm3,0xf0(%rsp)
   15f98:	call   10e00 <operator new(unsigned long)@plt>
   15f9d:	mov    %rax,%rdx
   15fa0:	mov    0x1c651(%rip),%rcx        # 325f8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x70>
   15fa7:	movapd 0x1c771(%rip),%xmm1        # 32720 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x198>
   15faf:	pxor   %xmm0,%xmm0
   15fb3:	movabs $0x100000001,%rax
   15fbd:	movl   $0x0,0x18(%rdx)
   15fc4:	lea    0x10(%rdx),%rsi
   15fc8:	mov    %rax,0x8(%rdx)
   15fcc:	lea    0x10(%r14),%rax
   15fd0:	mov    %rax,(%rdx)
   15fd3:	lea    0x10(%r13),%rax
   15fd7:	mov    %rax,0x10(%rdx)
   15fdb:	movq   $0x0,0x30(%rdx)
   15fe3:	movb   $0x1,0x38(%rdx)
   15fe7:	movq   $0x0,0x40(%rdx)
   15fef:	movl   $0x0,0x58(%rdx)
   15ff6:	movl   $0x0,0x70(%rdx)
   15ffd:	movq   $0x0,0x80(%rdx)
   16008:	movl   $0x0,0x88(%rdx)
   16012:	mov    %rcx,0xa0(%rdx)
   16019:	movl   $0x2,0xb0(%rdx)
   16023:	movups %xmm0,0x20(%rdx)
   16027:	movups %xmm0,0x48(%rdx)
   1602b:	movups %xmm0,0x60(%rdx)
   1602f:	movups %xmm1,0x90(%rdx)
   16036:	mov    %rsi,(%rsp)
   1603a:	mov    %rdx,0x10(%rsp)
   1603f:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   16044:	mov    (%rsp),%rsi
   16048:	mov    0x10(%rsp),%rdx
   1604d:	mov    $0xb8,%edi
   16052:	mov    %rax,0x70(%rsi)
   16056:	movq   %rsi,%xmm4
   1605b:	movq   %rdx,%xmm2
   16060:	punpcklqdq %xmm2,%xmm4
   16064:	movaps %xmm4,0x60(%rsp)
   16069:	movaps %xmm4,0x100(%rsp)
   16071:	call   10e00 <operator new(unsigned long)@plt>
   16076:	mov    %rax,%rdx
   16079:	mov    0x1c578(%rip),%rsi        # 325f8 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x70>
   16080:	movapd 0x1c698(%rip),%xmm7        # 32720 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x198>
   16088:	pxor   %xmm0,%xmm0
   1608c:	movabs $0x100000001,%rax
   16096:	movl   $0x0,0x18(%rdx)
   1609d:	mov    %rax,0x8(%rdx)
   160a1:	lea    0x10(%r14),%rax
   160a5:	lea    0x10(%rdx),%r14
   160a9:	mov    %rax,(%rdx)
   160ac:	lea    0x10(%r13),%rax
   160b0:	mov    %rax,0x10(%rdx)
   160b4:	movq   $0x0,0x30(%rdx)
   160bc:	movb   $0x1,0x38(%rdx)
   160c0:	movq   $0x0,0x40(%rdx)
   160c8:	movl   $0x0,0x58(%rdx)
   160cf:	movl   $0x0,0x70(%rdx)
   160d6:	movq   $0x0,0x80(%rdx)
   160e1:	movl   $0x0,0x88(%rdx)
   160eb:	mov    %rsi,0xa0(%rdx)
   160f2:	movl   $0x4,0xb0(%rdx)
   160fc:	movups %xmm0,0x20(%rdx)
   16100:	movups %xmm0,0x48(%rdx)
   16104:	movups %xmm0,0x60(%rdx)
   16108:	movups %xmm7,0x90(%rdx)
   1610f:	mov    %rdx,(%rsp)
   16113:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   16118:	mov    (%rsp),%rdx
   1611c:	movq   %r14,%xmm5
   16121:	mov    $0x90,%edi
   16126:	mov    %rax,0x70(%r14)
   1612a:	movq   %rdx,%xmm4
   1612f:	punpcklqdq %xmm4,%xmm5
   16133:	movaps %xmm5,0x40(%rsp)
   16138:	movaps %xmm5,0x110(%rsp)
   16140:	call   10e00 <operator new(unsigned long)@plt>
   16145:	mov    0x25d7c(%rip),%r14        # 3bec8 <vtable for std::_Sp_counted_ptr_inplace<arx::hw_interface::MotorType2, std::allocator<arx::hw_interface::MotorType2>, (__gnu_cxx::_Lock_policy)2>@@Base+0x4e0>
   1614c:	mov    %rax,%rdx
   1614f:	mov    0x25e12(%rip),%r13        # 3bf68 <vtable for arx::hw_interface::MotorType2@@Base+0x548>
   16156:	pxor   %xmm0,%xmm0
   1615a:	movabs $0x100000001,%rax
   16164:	movb   $0x1,0x38(%rdx)
   16168:	lea    0x10(%rdx),%rcx
   1616c:	mov    %rax,0x8(%rdx)
   16170:	lea    0x10(%r14),%rax
   16174:	mov    %rax,(%rdx)
   16177:	lea    0x10(%r13),%rax
   1617b:	movl   $0x0,0x18(%rdx)
   16182:	mov    %rax,0x10(%rdx)
   16186:	movq   $0x0,0x40(%rdx)
   1618e:	movl   $0x0,0x58(%rdx)
   16195:	movl   $0x1,0x70(%rdx)
   1619c:	movq   $0x0,0x78(%rdx)
   161a4:	movl   $0x5,0x88(%rdx)
   161ae:	movups %xmm0,0x48(%rdx)
   161b2:	movups %xmm0,0x60(%rdx)
   161b6:	mov    %rcx,(%rsp)
   161ba:	mov    %rdx,0x10(%rsp)
   161bf:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   161c4:	mov    (%rsp),%rcx
   161c8:	mov    0x10(%rsp),%rdx
   161cd:	mov    $0x90,%edi
   161d2:	mov    %rax,0x68(%rcx)
   161d6:	movq   %rcx,%xmm6
   161db:	movq   %rdx,%xmm5
   161e0:	punpcklqdq %xmm5,%xmm6
   161e4:	movaps %xmm6,0x50(%rsp)
   161e9:	movaps %xmm6,0x120(%rsp)
   161f1:	call   10e00 <operator new(unsigned long)@plt>
   161f6:	mov    %rax,%rdx
   161f9:	pxor   %xmm0,%xmm0
   161fd:	movabs $0x100000001,%rax
   16207:	mov    %rax,0x8(%rdx)
   1620b:	lea    0x10(%r14),%rax
   1620f:	lea    0x10(%rdx),%rsi
   16213:	mov    %rax,(%rdx)
   16216:	lea    0x10(%r13),%rax
   1621a:	movl   $0x0,0x18(%rdx)
   16221:	mov    %rax,0x10(%rdx)
   16225:	movb   $0x1,0x38(%rdx)
   16229:	movq   $0x0,0x40(%rdx)
   16231:	movl   $0x0,0x58(%rdx)
   16238:	movl   $0x1,0x70(%rdx)
   1623f:	movq   $0x0,0x78(%rdx)
   16247:	movl   $0x6,0x88(%rdx)
   16251:	movups %xmm0,0x48(%rdx)
   16255:	movups %xmm0,0x60(%rdx)
   16259:	mov    %rsi,(%rsp)
   1625d:	mov    %rdx,0x10(%rsp)
   16262:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   16267:	mov    (%rsp),%rsi
   1626b:	mov    0x10(%rsp),%rdx
   16270:	mov    $0x90,%edi
   16275:	mov    %rax,0x68(%rsi)
   16279:	movq   %rsi,%xmm7
   1627e:	movq   %rdx,%xmm6
   16283:	punpcklqdq %xmm6,%xmm7
   16287:	movaps %xmm7,0x20(%rsp)
   1628c:	movaps %xmm7,0x130(%rsp)
   16294:	call   10e00 <operator new(unsigned long)@plt>
   16299:	mov    %rax,%rdx
   1629c:	pxor   %xmm0,%xmm0
   162a0:	movabs $0x100000001,%rax
   162aa:	mov    %rax,0x8(%rdx)
   162ae:	lea    0x10(%r14),%rax
   162b2:	lea    0x10(%rdx),%rcx
   162b6:	mov    %rax,(%rdx)
   162b9:	lea    0x10(%r13),%rax
   162bd:	movl   $0x0,0x18(%rdx)
   162c4:	mov    %rax,0x10(%rdx)
   162c8:	movb   $0x1,0x38(%rdx)
   162cc:	movq   $0x0,0x40(%rdx)
   162d4:	movl   $0x0,0x58(%rdx)
   162db:	movl   $0x1,0x70(%rdx)
   162e2:	movq   $0x0,0x78(%rdx)
   162ea:	movl   $0x7,0x88(%rdx)
   162f4:	movups %xmm0,0x48(%rdx)
   162f8:	movups %xmm0,0x60(%rdx)
   162fc:	mov    %rcx,(%rsp)
   16300:	mov    %rdx,0x10(%rsp)
   16305:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   1630a:	mov    (%rsp),%rcx
   1630e:	mov    0x10(%rsp),%rdx
   16313:	mov    $0x90,%edi
   16318:	mov    %rax,0x68(%rcx)
   1631c:	movq   %rcx,%xmm1
   16321:	movq   %rdx,%xmm2
   16326:	punpcklqdq %xmm2,%xmm1
   1632a:	movaps %xmm1,0x10(%rsp)
   1632f:	movaps %xmm1,0x140(%rsp)
   16337:	call   10e00 <operator new(unsigned long)@plt>
   1633c:	mov    %rax,%rdx
   1633f:	pxor   %xmm0,%xmm0
   16343:	movabs $0x100000001,%rax
   1634d:	mov    %rax,0x8(%rdx)
   16351:	lea    0x10(%r14),%rax
   16355:	lea    0x10(%rdx),%r14
   16359:	mov    %rax,(%rdx)
   1635c:	lea    0x10(%r13),%rax
   16360:	movl   $0x0,0x18(%rdx)
   16367:	mov    %rax,0x10(%rdx)
   1636b:	movb   $0x1,0x38(%rdx)
   1636f:	movq   $0x0,0x40(%rdx)
   16377:	movl   $0x0,0x58(%rdx)
   1637e:	movl   $0x1,0x70(%rdx)
   16385:	movq   $0x0,0x78(%rdx)
   1638d:	movl   $0x8,0x88(%rdx)
   16397:	movups %xmm0,0x48(%rdx)
   1639b:	movups %xmm0,0x60(%rdx)
   1639f:	mov    %rdx,(%rsp)
   163a3:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   163a8:	mov    (%rsp),%rdx
   163ac:	movq   %r14,%xmm2
   163b1:	movq   $0x0,0x438(%rbx)
   163bc:	mov    %rax,0x68(%r14)
   163c0:	pxor   %xmm0,%xmm0
   163c4:	mov    $0x70,%edi
   163c9:	movq   %rdx,%xmm1
   163ce:	movups %xmm0,0x428(%rbx)
   163d5:	punpcklqdq %xmm1,%xmm2
   163d9:	movaps %xmm2,(%rsp)
   163dd:	movaps %xmm2,0x150(%rsp)
   163e5:	call   10e00 <operator new(unsigned long)@plt>
   163ea:	mov    0x25b37(%rip),%rdi        # 3bf28 <__pthread_key_create>
   163f1:	lea    0x70(%rax),%r8
   163f5:	mov    %rax,0x428(%rbx)
   163fc:	mov    %r8,0x438(%rbx)
   16403:	test   %rdi,%rdi
   16406:	je     167f8 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xf28>
   1640c:	mov    %r12,%rdx
   1640f:	lea    0x160(%rsp),%rsi
   16417:	nopw   0x0(%rax,%rax,1)
   16420:	movdqa (%rdx),%xmm3
   16424:	mov    0x8(%rdx),%rcx
   16428:	movups %xmm3,(%rax)
   1642b:	test   %rcx,%rcx
   1642e:	je     16435 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xb65>
   16430:	lock addl $0x1,0x8(%rcx)
   16435:	add    $0x10,%rdx
   16439:	add    $0x10,%rax
   1643d:	cmp    %rsi,%rdx
   16440:	jne    16420 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xb50>
   16442:	mov    %r8,0x430(%rbx)
   16449:	lea    0x150(%rsp),%r14
   16451:	test   %rdi,%rdi
   16454:	jne    1646c <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xb9c>
   16456:	jmp    168c0 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xff0>
   1645b:	nopl   0x0(%rax,%rax,1)
   16460:	lea    -0x10(%r14),%rax
   16464:	cmp    %r12,%r14
   16467:	je     164a8 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xbd8>
   16469:	mov    %rax,%r14
   1646c:	mov    0x8(%r14),%r13
   16470:	test   %r13,%r13
   16473:	je     16460 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xb90>
   16475:	lock subl $0x1,0x8(%r13)
   1647b:	jne    16460 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xb90>
   1647d:	mov    0x0(%r13),%rax
   16481:	mov    %r13,%rdi
   16484:	call   *0x10(%rax)
   16487:	lock subl $0x1,0xc(%r13)
   1648d:	jne    16460 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xb90>
   1648f:	mov    0x0(%r13),%rax
   16493:	mov    %r13,%rdi
   16496:	call   *0x18(%rax)
   16499:	lea    -0x10(%r14),%rax
   1649d:	cmp    %r12,%r14
   164a0:	jne    16469 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0xb99>
   164a2:	nopw   0x0(%rax,%rax,1)
   164a8:	pxor   %xmm0,%xmm0
   164ac:	mov    $0x30,%edi
   164b1:	movups %xmm0,0x440(%rbx)
   164b8:	movups %xmm0,0x450(%rbx)
   164bf:	movups %xmm0,0x460(%rbx)
   164c6:	movups %xmm0,0x470(%rbx)
   164cd:	movaps %xmm0,0x480(%rbx)
   164d4:	movaps %xmm0,0x490(%rbx)
   164db:	pxor   %xmm0,%xmm0
   164df:	movaps %xmm0,0x80(%rsp)
   164e7:	movaps %xmm0,0x90(%rsp)
   164ef:	movaps %xmm0,0xa0(%rsp)
   164f7:	pxor   %xmm0,%xmm0
   164fb:	movups %xmm0,0x4a0(%rbx)
   16502:	movups %xmm0,0x4b0(%rbx)
   16509:	movups %xmm0,0x4c0(%rbx)
   16510:	call   10e00 <operator new(unsigned long)@plt>
   16515:	lea    0x30(%rax),%rdx
   16519:	mov    %rax,0x4b8(%rbx)
   16520:	movdqa 0x80(%rsp),%xmm7
   16529:	lea    0x4d0(%rbx),%r12
   16530:	movdqa 0x90(%rsp),%xmm4
   16539:	mov    %rdx,0x4c8(%rbx)
   16540:	mov    %r12,%rdi
   16543:	movdqa 0xa0(%rsp),%xmm5
   1654c:	mov    %rdx,0x4c0(%rbx)
   16553:	movups %xmm7,(%rax)
   16556:	movups %xmm4,0x10(%rax)
   1655a:	movups %xmm5,0x20(%rax)
   1655e:	call   105f0 <KDL::JntArray::JntArray()@plt>
   16563:	movq   $0x0,0x4f0(%rbx)
   1656e:	pxor   %xmm0,%xmm0
   16572:	mov    $0x30,%edi
   16577:	movups %xmm0,0x4e0(%rbx)
   1657e:	call   10e00 <operator new(unsigned long)@plt>
   16583:	lea    0x30(%rax),%rdx
   16587:	movdqa 0x1bb91(%rip),%xmm6        # 32120 <C.3.322627>
   1658f:	movdqa 0x1bb99(%rip),%xmm3        # 32130 <C.3.322627+0x10>
   16597:	mov    %rax,0x4e0(%rbx)
   1659e:	mov    %rdx,0x4f0(%rbx)
   165a5:	pxor   %xmm0,%xmm0
   165a9:	movdqa 0x1bb8f(%rip),%xmm1        # 32140 <C.3.322627+0x20>
   165b1:	mov    $0x30,%edi
   165b6:	mov    %rdx,0x4e8(%rbx)
   165bd:	movq   $0x0,0x508(%rbx)
   165c8:	movups %xmm6,(%rax)
   165cb:	movups %xmm3,0x10(%rax)
   165cf:	movups %xmm1,0x20(%rax)
   165d3:	movups %xmm0,0x4f8(%rbx)
   165da:	call   10e00 <operator new(unsigned long)@plt>
   165df:	lea    0x30(%rax),%rdx
   165e3:	movdqa 0x1baf5(%rip),%xmm2        # 320e0 <C.4.322631>
   165eb:	movdqa 0x1bafd(%rip),%xmm7        # 320f0 <C.4.322631+0x10>
   165f3:	mov    %rax,0x4f8(%rbx)
   165fa:	mov    %rdx,0x508(%rbx)
   16601:	pxor   %xmm0,%xmm0
   16605:	movdqa 0x1baf3(%rip),%xmm4        # 32100 <C.4.322631+0x20>
   1660d:	mov    $0x30,%edi
   16612:	mov    %rdx,0x500(%rbx)
   16619:	movq   $0x0,0x520(%rbx)
   16624:	movups %xmm2,(%rax)
   16627:	movups %xmm7,0x10(%rax)
   1662b:	movups %xmm4,0x20(%rax)
   1662f:	movups %xmm0,0x510(%rbx)
   16636:	call   10e00 <operator new(unsigned long)@plt>
   1663b:	lea    0x30(%rax),%rdx
   1663f:	movdqa 0x1ba59(%rip),%xmm5        # 320a0 <C.5.322635>
   16647:	movdqa 0x1ba61(%rip),%xmm6        # 320b0 <C.5.322635+0x10>
   1664f:	mov    %rax,0x510(%rbx)
   16656:	mov    %rdx,0x520(%rbx)
   1665d:	pxor   %xmm0,%xmm0
   16661:	movdqa 0x1ba57(%rip),%xmm3        # 320c0 <C.5.322635+0x20>
   16669:	mov    $0x30,%edi
   1666e:	mov    %rdx,0x518(%rbx)
   16675:	movq   $0x0,0x538(%rbx)
   16680:	movups %xmm5,(%rax)
   16683:	movups %xmm6,0x10(%rax)
   16687:	movups %xmm3,0x20(%rax)
   1668b:	movups %xmm0,0x528(%rbx)
   16692:	call   10e00 <operator new(unsigned long)@plt>
   16697:	lea    0x30(%rax),%rdx
   1669b:	pxor   %xmm0,%xmm0
   1669f:	movdqa 0x1b9b9(%rip),%xmm1        # 32060 <C.6.322639>
   166a7:	movdqa 0x1b9c1(%rip),%xmm2        # 32070 <C.6.322639+0x10>
   166af:	movdqa 0x1b9c9(%rip),%xmm7        # 32080 <C.6.322639+0x20>
   166b7:	mov    %rax,0x528(%rbx)
   166be:	mov    $0x30,%edi
   166c3:	mov    %rdx,0x538(%rbx)
   166ca:	mov    %rdx,0x530(%rbx)
   166d1:	movq   $0x0,0x550(%rbx)
   166dc:	movaps %xmm0,0xf0(%rsp)
   166e4:	movaps %xmm0,0x100(%rsp)
   166ec:	movaps %xmm0,0x110(%rsp)
   166f4:	pxor   %xmm0,%xmm0
   166f8:	movups %xmm1,(%rax)
   166fb:	movups %xmm2,0x10(%rax)
   166ff:	movups %xmm7,0x20(%rax)
   16703:	movups %xmm0,0x540(%rbx)
   1670a:	call   10e00 <operator new(unsigned long)@plt>
   1670f:	movapd 0x1c019(%rip),%xmm0        # 32730 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x1a8>
   16717:	lea    0x30(%rax),%rdx
   1671b:	movq   0x1bf2d(%rip),%xmm2        # 32650 <std::_Sp_make_shared_tag::_S_ti()::__tag+0xc8>
   16723:	mov    %rax,0x540(%rbx)
   1672a:	movapd 0x1c00e(%rip),%xmm1        # 32740 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x1b8>
   16732:	mov    %rdx,0x550(%rbx)
   16739:	mov    %rbx,%rdi
   1673c:	movdqa 0xf0(%rsp),%xmm4
   16745:	mov    %rdx,0x548(%rbx)
   1674c:	movdqa 0x100(%rsp),%xmm5
   16755:	movups %xmm0,0x558(%rbx)
   1675c:	movdqa 0x110(%rsp),%xmm6
   16765:	pxor   %xmm0,%xmm0
   16769:	movups %xmm4,(%rax)
   1676c:	movups %xmm5,0x10(%rax)
   16770:	movups %xmm6,0x20(%rax)
   16774:	movaps %xmm2,0xe0(%rbx)
   1677b:	movaps %xmm0,0xf0(%rbx)
   16782:	movaps %xmm1,0x100(%rbx)
   16789:	movaps %xmm0,0x110(%rbx)
   16790:	movaps %xmm0,0x120(%rbx)
   16797:	movaps %xmm2,0x130(%rbx)
   1679e:	movaps %xmm0,0x140(%rbx)
   167a5:	movaps %xmm1,0x150(%rbx)
   167ac:	call   111c0 <arx::x5::ControllerBase::Init()@plt>
   167b1:	mov    0x168(%rsp),%rax
   167b9:	xor    %fs:0x28,%rax
   167c2:	jne    16b73 <arx::x5::ControllerBase::ControllerBase(std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, std::__cxx11::basic_string<char, std::char_traits<char>, std::allocator<char> > const&, int)+0x12a3>
   167c8:	add    $0x178,%rsp
   167cf:	pop    %rbx
   167d0:	pop    %rbp
   167d1:	pop    %r12
   167d3:	pop    %r13
   167d5:	pop    %r14
   167d7:	pop    %r15
   167d9:	ret
0000000000019dd0 <arx::x5::InterfacesPy::arx_x(double, double, double)>:
   19dd0:	endbr64
   19dd4:	movsd  0x18a4c(%rip),%xmm2        # 32828 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x2a0>
   19ddc:	mov    (%rdi),%rax
   19ddf:	divsd  %xmm2,%xmm0
   19de3:	divsd  %xmm2,%xmm1
   19de7:	movsd  0x18801(%rip),%xmm2        # 325f0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x68>
   19def:	comisd %xmm2,%xmm0
   19df3:	jbe    19e18 <arx::x5::InterfacesPy::arx_x(double, double, double)+0x48>
   19df5:	movsd  %xmm2,0x178(%rax)
   19dfd:	movsd  0x187db(%rip),%xmm0        # 325e0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x58>
   19e05:	comisd %xmm0,%xmm1
   19e09:	jbe    19e38 <arx::x5::InterfacesPy::arx_x(double, double, double)+0x68>
   19e0b:	movsd  %xmm0,0x180(%rax)
   19e13:	ret
   19e14:	nopl   0x0(%rax)
   19e18:	pxor   %xmm2,%xmm2
   19e1c:	comisd %xmm0,%xmm2
   19e20:	ja     19e60 <arx::x5::InterfacesPy::arx_x(double, double, double)+0x90>
   19e22:	movsd  %xmm0,0x178(%rax)
   19e2a:	movsd  0x187ae(%rip),%xmm0        # 325e0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x58>
   19e32:	comisd %xmm0,%xmm1
   19e36:	ja     19e0b <arx::x5::InterfacesPy::arx_x(double, double, double)+0x3b>
   19e38:	pxor   %xmm0,%xmm0
   19e3c:	comisd %xmm1,%xmm0
   19e40:	ja     19e50 <arx::x5::InterfacesPy::arx_x(double, double, double)+0x80>
   19e42:	movsd  %xmm1,0x180(%rax)
   19e4a:	ret
   19e4b:	nopl   0x0(%rax,%rax,1)
   19e50:	movq   $0x0,0x180(%rax)
   19e5b:	ret
   19e5c:	nopl   0x0(%rax)
   19e60:	movq   $0x0,0x178(%rax)
   19e6b:	jmp    19dfd <arx::x5::InterfacesPy::arx_x(double, double, double)+0x2d>
   19e6d:	nopl   (%rax)

0000000000029a30 <arx::solve::Interpolation(double*, double*, double*, double, double, double)>:
   29a30:	endbr64
   29a34:	sub    $0x28,%rsp
   29a38:	cvtsd2ss %xmm1,%xmm1
   29a3c:	pxor   %xmm3,%xmm3
   29a40:	pxor   %xmm2,%xmm2
   29a44:	movaps %xmm1,%xmm5
   29a47:	cvtsd2ss (%rsi),%xmm3
   29a4b:	cvtsd2ss (%rdi),%xmm2
   29a4f:	subss  %xmm3,%xmm2
   29a53:	mulss  %xmm1,%xmm5
   29a57:	pxor   %xmm6,%xmm6
   29a5b:	cvtsd2ss %xmm0,%xmm0
   29a5f:	addss  %xmm0,%xmm0
   29a63:	comiss %xmm6,%xmm2
   29a66:	movaps %xmm5,%xmm4
   29a69:	divss  %xmm0,%xmm4
   29a6d:	jbe    29ab0 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x80>
   29a6f:	comiss %xmm2,%xmm4
   29a72:	ja     29af8 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0xc8>
   29a78:	movaps %xmm4,%xmm7
   29a7b:	addss  %xmm4,%xmm7
   29a7f:	comiss %xmm7,%xmm2
   29a82:	jbe    29b80 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x150>
   29a88:	pxor   %xmm0,%xmm0
   29a8c:	cvtss2sd %xmm1,%xmm0
   29a90:	mulss  0x9418(%rip),%xmm1        # 32eb0 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x928>
   29a98:	movsd  %xmm0,(%rdx)
   29a9c:	addss  %xmm3,%xmm1
   29aa0:	cvtss2sd %xmm1,%xmm1
   29aa4:	movsd  %xmm1,(%rsi)
   29aa8:	add    $0x28,%rsp
   29aac:	ret
   29aad:	nopl   (%rax)
   29ab0:	movss  0x92c8(%rip),%xmm7        # 32d80 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x7f8>
   29ab8:	xorps  %xmm7,%xmm2
   29abb:	comiss %xmm2,%xmm4
   29abe:	ja     29b30 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x100>
   29ac0:	movaps %xmm4,%xmm8
   29ac4:	xorps  %xmm7,%xmm1
   29ac7:	addss  %xmm4,%xmm8
   29acc:	comiss %xmm8,%xmm2
   29ad0:	ja     29a88 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x58>
   29ad2:	subss  %xmm4,%xmm2
   29ad6:	mulss  %xmm2,%xmm0
   29ada:	subss  %xmm0,%xmm5
   29ade:	ucomiss %xmm5,%xmm6
   29ae1:	movaps %xmm5,%xmm1
   29ae4:	sqrtss %xmm1,%xmm1
   29ae8:	ja     29bd5 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x1a5>
   29aee:	xorps  %xmm7,%xmm1
   29af1:	jmp    29a88 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x58>
   29af3:	nopl   0x0(%rax,%rax,1)
   29af8:	mulss  %xmm2,%xmm0
   29afc:	ucomiss %xmm0,%xmm6
   29aff:	movaps %xmm0,%xmm1
   29b02:	sqrtss %xmm1,%xmm1
   29b06:	jbe    29a88 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x58>
   29b0c:	mov    %rdx,0x18(%rsp)
   29b11:	mov    %rsi,0x10(%rsp)
   29b16:	movss  %xmm3,0xc(%rsp)
   29b1c:	movss  %xmm1,0x8(%rsp)
   29b22:	jmp    29bb5 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x185>
   29b27:	nopw   0x0(%rax,%rax,1)
   29b30:	mulss  %xmm2,%xmm0
   29b34:	ucomiss %xmm0,%xmm6
   29b37:	movaps %xmm0,%xmm1
   29b3a:	sqrtss %xmm1,%xmm1
   29b3e:	jbe    29aee <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0xbe>
   29b40:	mov    %rdx,0x18(%rsp)
   29b45:	mov    %rsi,0x10(%rsp)
   29b4a:	movss  %xmm3,0xc(%rsp)
   29b50:	movss  %xmm1,0x8(%rsp)
   29b56:	call   11540 <sqrtf@plt>
   29b5b:	mov    0x18(%rsp),%rdx
   29b60:	mov    0x10(%rsp),%rsi
   29b65:	movss  0x9213(%rip),%xmm7        # 32d80 <std::_Sp_make_shared_tag::_S_ti()::__tag+0x7f8>
   29b6d:	movss  0xc(%rsp),%xmm3
   29b73:	movss  0x8(%rsp),%xmm1
   29b79:	jmp    29aee <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0xbe>
   29b7e:	xchg   %ax,%ax
   29b80:	subss  %xmm4,%xmm2
   29b84:	mulss  %xmm2,%xmm0
   29b88:	subss  %xmm0,%xmm5
   29b8c:	ucomiss %xmm5,%xmm6
   29b8f:	movaps %xmm5,%xmm1
   29b92:	sqrtss %xmm1,%xmm1
   29b96:	jbe    29a88 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x58>
   29b9c:	mov    %rdx,0x18(%rsp)
   29ba1:	movaps %xmm5,%xmm0
   29ba4:	mov    %rsi,0x10(%rsp)
   29ba9:	movss  %xmm3,0xc(%rsp)
   29baf:	movss  %xmm1,0x8(%rsp)
   29bb5:	call   11540 <sqrtf@plt>
   29bba:	movss  0x8(%rsp),%xmm1
   29bc0:	movss  0xc(%rsp),%xmm3
   29bc6:	mov    0x10(%rsp),%rsi
   29bcb:	mov    0x18(%rsp),%rdx
   29bd0:	jmp    29a88 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x58>
   29bd5:	mov    %rdx,0x18(%rsp)
   29bda:	movaps %xmm5,%xmm0
   29bdd:	mov    %rsi,0x10(%rsp)
   29be2:	movss  %xmm3,0xc(%rsp)
   29be8:	movss  %xmm1,0x8(%rsp)
   29bee:	jmp    29b56 <arx::solve::Interpolation(double*, double*, double*, double, double, double)+0x126>
   29bf3:	data16 cs nopw 0x0(%rax,%rax,1)
   29bfe:	xchg   %ax,%ax

000000000002d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>:
   2d88f:	endbr64
   2d893:	push   %rbp
   2d894:	mov    %rsp,%rbp
   2d897:	movss  %xmm0,-0x14(%rbp)
   2d89c:	movss  %xmm1,-0x18(%rbp)
   2d8a1:	movss  %xmm2,-0x1c(%rbp)
   2d8a6:	mov    %edi,-0x20(%rbp)
   2d8a9:	movss  -0x1c(%rbp),%xmm0
   2d8ae:	subss  -0x18(%rbp),%xmm0
   2d8b3:	movss  %xmm0,-0x8(%rbp)
   2d8b8:	movss  -0x18(%rbp),%xmm0
   2d8bd:	movss  %xmm0,-0x4(%rbp)
   2d8c2:	movss  -0x14(%rbp),%xmm0
   2d8c7:	movaps %xmm0,%xmm1
   2d8ca:	subss  -0x4(%rbp),%xmm1
   2d8cf:	mov    -0x20(%rbp),%eax
   2d8d2:	mov    $0x1,%edx
   2d8d7:	mov    %eax,%ecx
   2d8d9:	shl    %cl,%edx
   2d8db:	mov    %edx,%eax
   2d8dd:	sub    $0x1,%eax
   2d8e0:	pxor   %xmm0,%xmm0
   2d8e4:	cvtsi2ss %eax,%xmm0
   2d8e8:	mulss  %xmm1,%xmm0
   2d8ec:	divss  -0x8(%rbp),%xmm0
   2d8f1:	cvttss2si %xmm0,%eax
   2d8f5:	pop    %rbp
   2d8f6:	ret

000000000002d8f7 <(anonymous namespace)::uint_to_float(int, float, float, int)>:
   2d8f7:	endbr64
   2d8fb:	push   %rbp
   2d8fc:	mov    %rsp,%rbp
   2d8ff:	mov    %edi,-0x14(%rbp)
   2d902:	movss  %xmm0,-0x18(%rbp)
   2d907:	movss  %xmm1,-0x1c(%rbp)
   2d90c:	mov    %esi,-0x20(%rbp)
   2d90f:	movss  -0x1c(%rbp),%xmm0
   2d914:	subss  -0x18(%rbp),%xmm0
   2d919:	movss  %xmm0,-0x8(%rbp)
   2d91e:	movss  -0x18(%rbp),%xmm0
   2d923:	movss  %xmm0,-0x4(%rbp)
   2d928:	pxor   %xmm0,%xmm0
   2d92c:	cvtsi2ssl -0x14(%rbp),%xmm0
   2d931:	mulss  -0x8(%rbp),%xmm0
   2d936:	mov    -0x20(%rbp),%eax
   2d939:	mov    $0x1,%edx
   2d93e:	mov    %eax,%ecx
   2d940:	shl    %cl,%edx
   2d942:	mov    %edx,%eax
   2d944:	sub    $0x1,%eax
   2d947:	pxor   %xmm1,%xmm1
   2d94b:	cvtsi2ss %eax,%xmm1
   2d94f:	divss  %xmm1,%xmm0
   2d953:	addss  -0x4(%rbp),%xmm0
   2d958:	pop    %rbp
   2d959:	ret

000000000002d95a <(anonymous namespace)::int_to_float(int, float, float, int)>:
   2d95a:	endbr64
   2d95e:	push   %rbp
   2d95f:	mov    %rsp,%rbp
   2d962:	mov    %edi,-0x4(%rbp)
   2d965:	movss  %xmm0,-0x8(%rbp)
   2d96a:	movss  %xmm1,-0xc(%rbp)
   2d96f:	mov    %esi,-0x10(%rbp)
   2d972:	pxor   %xmm0,%xmm0
   2d976:	cvtsi2ssl -0x4(%rbp),%xmm0
   2d97b:	movss  0x7465(%rip),%xmm2        # 34de8 <typeinfo name for arx::hw_interface::MotorDlcBase+0x28>
   2d983:	movaps %xmm0,%xmm1
   2d986:	divss  %xmm2,%xmm1
   2d98a:	movss  -0x8(%rbp),%xmm0
   2d98f:	subss  -0xc(%rbp),%xmm0
   2d994:	mulss  %xmm1,%xmm0
   2d998:	addss  -0xc(%rbp),%xmm0
   2d99d:	pop    %rbp
   2d99e:	ret

000000000002d99f <(anonymous namespace)::float32_to_float16(float*, unsigned short*)>:
   2d99f:	endbr64
   2d9a3:	push   %rbp
   2d9a4:	mov    %rsp,%rbp
   2d9a7:	mov    %rdi,-0x18(%rbp)
   2d9ab:	mov    %rsi,-0x20(%rbp)
   2d9af:	movw   $0x0,-0x2(%rbp)
   2d9b5:	mov    -0x18(%rbp),%rax
   2d9b9:	movss  (%rax),%xmm0
   2d9bd:	movss  %xmm0,0xf11f(%rip)        # 3cae4 <(anonymous namespace)::f32>
   2d9c5:	movzbl 0xf11b(%rip),%eax        # 3cae7 <(anonymous namespace)::f32+0x3>
   2d9cc:	movzbl %al,%eax
   2d9cf:	add    %eax,%eax
   2d9d1:	movzbl %al,%edx
   2d9d4:	movzbl 0xf10b(%rip),%eax        # 3cae6 <(anonymous namespace)::f32+0x2>
   2d9db:	shr    $0x7,%al
   2d9de:	movzbl %al,%eax
   2d9e1:	or     %edx,%eax
   2d9e3:	mov    %ax,-0x2(%rbp)
   2d9e7:	subw   $0x70,-0x2(%rbp)
   2d9ec:	movzwl -0x2(%rbp),%eax
   2d9f0:	shl    $0xa,%eax
   2d9f3:	mov    %eax,%edx
   2d9f5:	movzbl 0xf0ea(%rip),%eax        # 3cae6 <(anonymous namespace)::f32+0x2>
   2d9fc:	movzbl %al,%eax
   2d9ff:	shl    $0x3,%eax
   2da02:	and    $0x3f8,%ax
   2da06:	or     %eax,%edx
   2da08:	movzbl 0xf0d6(%rip),%eax        # 3cae5 <(anonymous namespace)::f32+0x1>
   2da0f:	shr    $0x5,%al
   2da12:	movzbl %al,%eax
   2da15:	or     %edx,%eax
   2da17:	mov    %eax,%edx
   2da19:	mov    -0x20(%rbp),%rax
   2da1d:	mov    %dx,(%rax)
   2da20:	mov    -0x20(%rbp),%rax
   2da24:	movzwl (%rax),%edx
   2da27:	mov    0xf0b7(%rip),%eax        # 3cae4 <(anonymous namespace)::f32>
   2da2d:	shr    $0x10,%eax
   2da30:	and    $0x8000,%ax
   2da34:	or     %eax,%edx
   2da36:	mov    -0x20(%rbp),%rax
   2da3a:	mov    %dx,(%rax)
   2da3d:	nop
   2da3e:	pop    %rbp
   2da3f:	ret

000000000002da40 <(anonymous namespace)::float16_to_float32(unsigned short*, float*)>:
   2da40:	endbr64
   2da44:	push   %rbp
   2da45:	mov    %rsp,%rbp
   2da48:	mov    %rdi,-0x18(%rbp)
   2da4c:	mov    %rsi,-0x20(%rbp)
   2da50:	movw   $0x0,-0x2(%rbp)
   2da56:	movl   $0x0,0xf084(%rip)        # 3cae4 <(anonymous namespace)::f32>
   2da60:	mov    -0x18(%rbp),%rax
   2da64:	movzwl (%rax),%eax
   2da67:	shr    $0xa,%ax
   2da6b:	and    $0x1f,%eax
   2da6e:	add    $0x70,%eax
   2da71:	mov    %ax,-0x2(%rbp)
   2da75:	movzwl -0x2(%rbp),%eax
   2da79:	shr    $1,%ax
   2da7c:	mov    %al,0xf065(%rip)        # 3cae7 <(anonymous namespace)::f32+0x3>
   2da82:	movzwl -0x2(%rbp),%eax
   2da86:	shl    $0x7,%eax
   2da89:	mov    %eax,%edx
   2da8b:	mov    -0x18(%rbp),%rax
   2da8f:	movzwl (%rax),%eax
   2da92:	shr    $0x3,%ax
   2da96:	and    $0x7f,%eax
   2da99:	or     %edx,%eax
   2da9b:	mov    %al,0xf045(%rip)        # 3cae6 <(anonymous namespace)::f32+0x2>
   2daa1:	mov    -0x18(%rbp),%rax
   2daa5:	movzwl (%rax),%eax
   2daa8:	movzwl %ax,%eax
   2daab:	shl    $0x6,%eax
   2daae:	mov    %al,0xf031(%rip)        # 3cae5 <(anonymous namespace)::f32+0x1>
   2dab4:	mov    0xf02a(%rip),%edx        # 3cae4 <(anonymous namespace)::f32>
   2daba:	mov    -0x18(%rbp),%rax
   2dabe:	movzwl (%rax),%eax
   2dac1:	movzwl %ax,%eax
   2dac4:	shl    $0x10,%eax
   2dac7:	and    $0x80000000,%eax
   2dacc:	or     %edx,%eax
   2dace:	mov    %eax,0xf010(%rip)        # 3cae4 <(anonymous namespace)::f32>
   2dad4:	movss  0xf008(%rip),%xmm0        # 3cae4 <(anonymous namespace)::f32>
   2dadc:	mov    -0x20(%rbp),%rax
   2dae0:	movss  %xmm0,(%rax)
   2dae4:	nop
   2dae5:	pop    %rbp
   2dae6:	ret
   2dae7:	nop

000000000002dae8 <arx::hw_interface::MotorType2::CanAnalyze(arx::hw_interface::CanFrame*)>:
   2dae8:	endbr64
   2daec:	push   %rbp
   2daed:	mov    %rsp,%rbp
   2daf0:	push   %rbx
   2daf1:	sub    $0x38,%rsp
   2daf5:	mov    %rdi,-0x38(%rbp)
   2daf9:	mov    %rsi,-0x40(%rbp)
   2dafd:	mov    -0x40(%rbp),%rax
   2db01:	mov    (%rax),%eax
   2db03:	test   %eax,%eax
   2db05:	jne    2dcdb <arx::hw_interface::MotorType2::CanAnalyze(arx::hw_interface::CanFrame*)+0x1f3>
   2db0b:	mov    -0x40(%rbp),%rax
   2db0f:	movzbl 0x8(%rax),%eax
   2db13:	movzbl %al,%eax
   2db16:	and    $0xf,%eax
   2db19:	mov    %eax,%edx
   2db1b:	mov    -0x38(%rbp),%rax
   2db1f:	mov    0x78(%rax),%eax
   2db22:	cmp    %eax,%edx
   2db24:	jne    2dcdb <arx::hw_interface::MotorType2::CanAnalyze(arx::hw_interface::CanFrame*)+0x1f3>
   2db2a:	mov    -0x40(%rbp),%rax
   2db2e:	movzbl 0x9(%rax),%eax
   2db32:	movzbl %al,%eax
   2db35:	shl    $0x8,%eax
   2db38:	mov    %eax,%edx
   2db3a:	mov    -0x40(%rbp),%rax
   2db3e:	movzbl 0xa(%rax),%eax
   2db42:	movzbl %al,%eax
   2db45:	or     %edx,%eax
   2db47:	mov    %eax,-0x24(%rbp)
   2db4a:	mov    -0x40(%rbp),%rax
   2db4e:	movzbl 0xb(%rax),%eax
   2db52:	movzbl %al,%eax
   2db55:	shl    $0x4,%eax
   2db58:	mov    %eax,%edx
   2db5a:	mov    -0x40(%rbp),%rax
   2db5e:	movzbl 0xc(%rax),%eax
   2db62:	shr    $0x4,%al
   2db65:	movzbl %al,%eax
   2db68:	or     %edx,%eax
   2db6a:	mov    %eax,-0x20(%rbp)
   2db6d:	mov    -0x40(%rbp),%rax
   2db71:	movzbl 0xc(%rax),%eax
   2db75:	movzbl %al,%eax
   2db78:	shl    $0x8,%eax
   2db7b:	and    $0xf00,%eax
   2db80:	mov    %eax,%edx
   2db82:	mov    -0x40(%rbp),%rax
   2db86:	movzbl 0xd(%rax),%eax
   2db8a:	movzbl %al,%eax
   2db8d:	or     %edx,%eax
   2db8f:	mov    %eax,-0x1c(%rbp)
   2db92:	mov    -0x40(%rbp),%rax
   2db96:	movzbl 0x8(%rax),%eax
   2db9a:	shr    $0x4,%al
   2db9d:	movzbl %al,%edx
   2dba0:	mov    -0x38(%rbp),%rax
   2dba4:	mov    %edx,0x60(%rax)
   2dba7:	mov    -0x24(%rbp),%eax
   2dbaa:	mov    $0x10,%esi
   2dbaf:	movss  0x7235(%rip),%xmm1        # 34dec <typeinfo name for arx::hw_interface::MotorDlcBase+0x2c>
   2dbb7:	mov    0x7233(%rip),%edx        # 34df0 <typeinfo name for arx::hw_interface::MotorDlcBase+0x30>
   2dbbd:	movd   %edx,%xmm0
   2dbc1:	mov    %eax,%edi
   2dbc3:	call   2d8f7 <(anonymous namespace)::uint_to_float(int, float, float, int)>
   2dbc8:	cvtss2sd %xmm0,%xmm0
   2dbcc:	movsd  %xmm0,-0x18(%rbp)
   2dbd1:	mov    -0x38(%rbp),%rax
   2dbd5:	movsd  0x40(%rax),%xmm1
   2dbda:	movsd  -0x18(%rbp),%xmm0
   2dbdf:	subsd  %xmm1,%xmm0
   2dbe3:	comisd 0x720d(%rip),%xmm0        # 34df8 <typeinfo name for arx::hw_interface::MotorDlcBase+0x38>
   2dbeb:	jbe    2dc00 <arx::hw_interface::MotorType2::CanAnalyze(arx::hw_interface::CanFrame*)+0x118>
   2dbed:	mov    -0x38(%rbp),%rax
   2dbf1:	mov    0x48(%rax),%eax
   2dbf4:	lea    -0x1(%rax),%edx
   2dbf7:	mov    -0x38(%rbp),%rax
   2dbfb:	mov    %edx,0x48(%rax)
   2dbfe:	jmp    2dc35 <arx::hw_interface::MotorType2::CanAnalyze(arx::hw_interface::CanFrame*)+0x14d>
   2dc00:	mov    -0x38(%rbp),%rax
   2dc04:	movsd  0x40(%rax),%xmm2
   2dc09:	movsd  -0x18(%rbp),%xmm0
   2dc0e:	movapd %xmm0,%xmm1
   2dc12:	subsd  %xmm2,%xmm1
   2dc16:	movsd  0x71e2(%rip),%xmm0        # 34e00 <typeinfo name for arx::hw_interface::MotorDlcBase+0x40>
   2dc1e:	comisd %xmm1,%xmm0
   2dc22:	jbe    2dc35 <arx::hw_interface::MotorType2::CanAnalyze(arx::hw_interface::CanFrame*)+0x14d>
   2dc24:	mov    -0x38(%rbp),%rax
   2dc28:	mov    0x48(%rax),%eax
   2dc2b:	lea    0x1(%rax),%edx
   2dc2e:	mov    -0x38(%rbp),%rax
   2dc32:	mov    %edx,0x48(%rax)
   2dc35:	mov    -0x38(%rbp),%rax
   2dc39:	movsd  -0x18(%rbp),%xmm0
   2dc3e:	movsd  %xmm0,0x40(%rax)
   2dc43:	mov    -0x38(%rbp),%rbx
   2dc47:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   2dc4c:	mov    %rax,0x68(%rbx)
   2dc50:	mov    -0x38(%rbp),%rax
   2dc54:	mov    0x48(%rax),%eax
   2dc57:	add    %eax,%eax
   2dc59:	pxor   %xmm1,%xmm1
   2dc5d:	cvtsi2ss %eax,%xmm1
   2dc61:	movss  0x7183(%rip),%xmm0        # 34dec <typeinfo name for arx::hw_interface::MotorDlcBase+0x2c>
   2dc69:	mulss  %xmm1,%xmm0
   2dc6d:	cvtss2sd %xmm0,%xmm0
   2dc71:	addsd  -0x18(%rbp),%xmm0
   2dc76:	mov    -0x38(%rbp),%rax
   2dc7a:	movsd  %xmm0,0x38(%rax)
   2dc7f:	mov    -0x20(%rbp),%eax
   2dc82:	mov    $0xc,%esi
   2dc87:	movss  0x7179(%rip),%xmm1        # 34e08 <typeinfo name for arx::hw_interface::MotorDlcBase+0x48>
   2dc8f:	mov    0x7177(%rip),%edx        # 34e0c <typeinfo name for arx::hw_interface::MotorDlcBase+0x4c>
   2dc95:	movd   %edx,%xmm0
   2dc99:	mov    %eax,%edi
   2dc9b:	call   2d8f7 <(anonymous namespace)::uint_to_float(int, float, float, int)>
   2dca0:	cvtss2sd %xmm0,%xmm0
   2dca4:	mov    -0x38(%rbp),%rax
   2dca8:	movsd  %xmm0,0x50(%rax)
   2dcad:	mov    -0x1c(%rbp),%eax
   2dcb0:	mov    $0xc,%esi
   2dcb5:	movss  0x7153(%rip),%xmm1        # 34e10 <typeinfo name for arx::hw_interface::MotorDlcBase+0x50>
   2dcbd:	mov    0x7151(%rip),%edx        # 34e14 <typeinfo name for arx::hw_interface::MotorDlcBase+0x54>
   2dcc3:	movd   %edx,%xmm0
   2dcc7:	mov    %eax,%edi
   2dcc9:	call   2d8f7 <(anonymous namespace)::uint_to_float(int, float, float, int)>
   2dcce:	cvtss2sd %xmm0,%xmm0
   2dcd2:	mov    -0x38(%rbp),%rax
   2dcd6:	movsd  %xmm0,0x58(%rax)
   2dcdb:	nop
   2dcdc:	mov    -0x8(%rbp),%rbx
   2dce0:	leave
   2dce1:	ret

000000000002dce2 <arx::hw_interface::MotorType2::GetMotorMsg()>:
   2dce2:	endbr64
   2dce6:	push   %rbp
   2dce7:	mov    %rsp,%rbp
   2dcea:	sub    $0x10,%rsp
   2dcee:	mov    %rdi,-0x8(%rbp)
   2dcf2:	mov    %rsi,-0x10(%rbp)
   2dcf6:	mov    -0x8(%rbp),%rax
   2dcfa:	mov    %rax,%rdi
   2dcfd:	call   10500 <arx::hw_interface::HybridJointStatus::HybridJointStatus()@plt>
   2dd02:	mov    -0x10(%rbp),%rax
   2dd06:	movsd  0x10(%rax),%xmm0
   2dd0b:	mov    -0x8(%rbp),%rax
   2dd0f:	movsd  %xmm0,(%rax)
   2dd13:	mov    -0x10(%rbp),%rax
   2dd17:	movsd  0x18(%rax),%xmm0
   2dd1c:	mov    -0x8(%rbp),%rax
   2dd20:	movsd  %xmm0,0x8(%rax)
   2dd25:	mov    -0x10(%rbp),%rax
   2dd29:	movsd  0x20(%rax),%xmm0
   2dd2e:	mov    -0x8(%rbp),%rax
   2dd32:	movsd  %xmm0,0x18(%rax)
   2dd37:	mov    -0x10(%rbp),%rax
   2dd3b:	movsd  0x20(%rax),%xmm0
   2dd40:	mov    -0x8(%rbp),%rax
   2dd44:	movsd  %xmm0,0x10(%rax)
   2dd49:	nop
   2dd4a:	mov    -0x8(%rbp),%rax
   2dd4e:	leave
   2dd4f:	ret

000000000002dd50 <arx::hw_interface::MotorType2::ExchangeMotorMsg()>:
   2dd50:	endbr64
   2dd54:	push   %rbp
   2dd55:	mov    %rsp,%rbp
   2dd58:	mov    %rdi,-0x8(%rbp)
   2dd5c:	mov    -0x8(%rbp),%rax
   2dd60:	movsd  0x38(%rax),%xmm0
   2dd65:	mov    -0x8(%rbp),%rax
   2dd69:	movsd  %xmm0,0x10(%rax)
   2dd6e:	mov    -0x8(%rbp),%rax
   2dd72:	movsd  0x50(%rax),%xmm0
   2dd77:	mov    -0x8(%rbp),%rax
   2dd7b:	movsd  %xmm0,0x18(%rax)
   2dd80:	mov    -0x8(%rbp),%rax
   2dd84:	movsd  0x58(%rax),%xmm0
   2dd89:	mov    -0x8(%rbp),%rax
   2dd8d:	movsd  %xmm0,0x20(%rax)
   2dd92:	mov    -0x8(%rbp),%rax
   2dd96:	mov    0x60(%rax),%edx
   2dd99:	mov    -0x8(%rbp),%rax
   2dd9d:	mov    %edx,0x8(%rax)
   2dda0:	mov    -0x8(%rbp),%rax
   2dda4:	mov    -0x8(%rbp),%rdx
   2dda8:	mov    0x68(%rdx),%rdx
   2ddac:	mov    %rdx,0x30(%rax)
   2ddb0:	nop
   2ddb1:	pop    %rbp
   2ddb2:	ret
   2ddb3:	nop

000000000002ddb4 <arx::hw_interface::MotorType2::packMotorMsg(arx::hw_interface::HybridJointCmd*)>:
   2ddb4:	endbr64
   2ddb8:	push   %rbp
   2ddb9:	mov    %rsp,%rbp
   2ddbc:	sub    $0x70,%rsp
   2ddc0:	mov    %rdi,-0x68(%rbp)
   2ddc4:	mov    %rsi,-0x70(%rbp)
   2ddc8:	mov    %fs:0x28,%rax
   2ddd1:	mov    %rax,-0x8(%rbp)
   2ddd5:	xor    %eax,%eax
   2ddd7:	mov    -0x68(%rbp),%rax
   2dddb:	mov    -0x70(%rbp),%rdx
   2dddf:	mov    0x18(%rdx),%rdx
   2dde3:	movsd  0x702d(%rip),%xmm0        # 34e18 <typeinfo name for arx::hw_interface::MotorDlcBase+0x58>
   2ddeb:	pxor   %xmm2,%xmm2
   2ddef:	movapd %xmm0,%xmm1
   2ddf3:	movq   %rdx,%xmm0
   2ddf8:	mov    %rax,%rdi
   2ddfb:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2de00:	movq   %xmm0,%rax
   2de05:	mov    %rax,-0x48(%rbp)
   2de09:	mov    -0x68(%rbp),%rax
   2de0d:	mov    -0x70(%rbp),%rdx
   2de11:	mov    0x20(%rdx),%rdx
   2de15:	movsd  0x7003(%rip),%xmm0        # 34e20 <typeinfo name for arx::hw_interface::MotorDlcBase+0x60>
   2de1d:	pxor   %xmm2,%xmm2
   2de21:	movapd %xmm0,%xmm1
   2de25:	movq   %rdx,%xmm0
   2de2a:	mov    %rax,%rdi
   2de2d:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2de32:	movq   %xmm0,%rax
   2de37:	mov    %rax,-0x40(%rbp)
   2de3b:	mov    -0x68(%rbp),%rax
   2de3f:	mov    -0x70(%rbp),%rdx
   2de43:	mov    (%rdx),%rdx
   2de46:	movsd  0x6fb2(%rip),%xmm1        # 34e00 <typeinfo name for arx::hw_interface::MotorDlcBase+0x40>
   2de4e:	movsd  0x6fa2(%rip),%xmm0        # 34df8 <typeinfo name for arx::hw_interface::MotorDlcBase+0x38>
   2de56:	movapd %xmm1,%xmm2
   2de5a:	movapd %xmm0,%xmm1
   2de5e:	movq   %rdx,%xmm0
   2de63:	mov    %rax,%rdi
   2de66:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2de6b:	movq   %xmm0,%rax
   2de70:	mov    %rax,-0x38(%rbp)
   2de74:	mov    -0x68(%rbp),%rax
   2de78:	mov    -0x70(%rbp),%rdx
   2de7c:	mov    0x8(%rdx),%rdx
   2de80:	movsd  0x6fa0(%rip),%xmm1        # 34e28 <typeinfo name for arx::hw_interface::MotorDlcBase+0x68>
   2de88:	movsd  0x6fa0(%rip),%xmm0        # 34e30 <typeinfo name for arx::hw_interface::MotorDlcBase+0x70>
   2de90:	movapd %xmm1,%xmm2
   2de94:	movapd %xmm0,%xmm1
   2de98:	movq   %rdx,%xmm0
   2de9d:	mov    %rax,%rdi
   2dea0:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2dea5:	movq   %xmm0,%rax
   2deaa:	mov    %rax,-0x30(%rbp)
   2deae:	mov    -0x68(%rbp),%rax
   2deb2:	mov    -0x70(%rbp),%rdx
   2deb6:	mov    0x10(%rdx),%rdx
   2deba:	movsd  0x6f76(%rip),%xmm1        # 34e38 <typeinfo name for arx::hw_interface::MotorDlcBase+0x78>
   2dec2:	movsd  0x6f76(%rip),%xmm0        # 34e40 <typeinfo name for arx::hw_interface::MotorDlcBase+0x80>
   2deca:	movapd %xmm1,%xmm2
   2dece:	movapd %xmm0,%xmm1
   2ded2:	movq   %rdx,%xmm0
   2ded7:	mov    %rax,%rdi
   2deda:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2dedf:	movq   %xmm0,%rax
   2dee4:	mov    %rax,-0x28(%rbp)
   2dee8:	pxor   %xmm3,%xmm3
   2deec:	cvtsd2ss -0x38(%rbp),%xmm3
   2def1:	movd   %xmm3,%eax
   2def5:	mov    $0x10,%edi
   2defa:	movss  0x6eea(%rip),%xmm2        # 34dec <typeinfo name for arx::hw_interface::MotorDlcBase+0x2c>
   2df02:	movss  0x6ee6(%rip),%xmm1        # 34df0 <typeinfo name for arx::hw_interface::MotorDlcBase+0x30>
   2df0a:	movd   %eax,%xmm0
   2df0e:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2df13:	mov    %ax,-0x52(%rbp)
   2df17:	pxor   %xmm4,%xmm4
   2df1b:	cvtsd2ss -0x30(%rbp),%xmm4
   2df20:	movd   %xmm4,%eax
   2df24:	mov    $0xc,%edi
   2df29:	movss  0x6ed7(%rip),%xmm2        # 34e08 <typeinfo name for arx::hw_interface::MotorDlcBase+0x48>
   2df31:	movss  0x6ed3(%rip),%xmm1        # 34e0c <typeinfo name for arx::hw_interface::MotorDlcBase+0x4c>
   2df39:	movd   %eax,%xmm0
   2df3d:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2df42:	mov    %ax,-0x50(%rbp)
   2df46:	pxor   %xmm5,%xmm5
   2df4a:	cvtsd2ss -0x48(%rbp),%xmm5
   2df4f:	movd   %xmm5,%eax
   2df53:	mov    $0xc,%edi
   2df58:	movss  0x6ee8(%rip),%xmm2        # 34e48 <typeinfo name for arx::hw_interface::MotorDlcBase+0x88>
   2df60:	pxor   %xmm1,%xmm1
   2df64:	movd   %eax,%xmm0
   2df68:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2df6d:	mov    %ax,-0x4e(%rbp)
   2df71:	pxor   %xmm6,%xmm6
   2df75:	cvtsd2ss -0x40(%rbp),%xmm6
   2df7a:	movd   %xmm6,%eax
   2df7e:	mov    $0xc,%edi
   2df83:	movss  0x6ec1(%rip),%xmm2        # 34e4c <typeinfo name for arx::hw_interface::MotorDlcBase+0x8c>
   2df8b:	pxor   %xmm1,%xmm1
   2df8f:	movd   %eax,%xmm0
   2df93:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2df98:	mov    %ax,-0x4c(%rbp)
   2df9c:	pxor   %xmm7,%xmm7
   2dfa0:	cvtsd2ss -0x28(%rbp),%xmm7
   2dfa5:	movd   %xmm7,%eax
   2dfa9:	mov    $0xc,%edi
   2dfae:	movss  0x6e5a(%rip),%xmm2        # 34e10 <typeinfo name for arx::hw_interface::MotorDlcBase+0x50>
   2dfb6:	movss  0x6e56(%rip),%xmm1        # 34e14 <typeinfo name for arx::hw_interface::MotorDlcBase+0x54>
   2dfbe:	movd   %eax,%xmm0
   2dfc2:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2dfc7:	mov    %ax,-0x4a(%rbp)
   2dfcb:	movb   $0x8,-0x1c(%rbp)
   2dfcf:	mov    -0x68(%rbp),%rax
   2dfd3:	mov    0x78(%rax),%eax
   2dfd6:	mov    %eax,-0x20(%rbp)
   2dfd9:	movzwl -0x52(%rbp),%eax
   2dfdd:	shr    $0x8,%ax
   2dfe1:	mov    %al,-0x18(%rbp)
   2dfe4:	movzwl -0x52(%rbp),%eax
   2dfe8:	mov    %al,-0x17(%rbp)
   2dfeb:	movzwl -0x50(%rbp),%eax
   2dfef:	shr    $0x4,%ax
   2dff3:	mov    %al,-0x16(%rbp)
   2dff6:	movzwl -0x50(%rbp),%eax
   2dffa:	shl    $0x4,%eax
   2dffd:	mov    %eax,%edx
   2dfff:	movzwl -0x4e(%rbp),%eax
   2e003:	shr    $0x8,%ax
   2e007:	or     %edx,%eax
   2e009:	mov    %al,-0x15(%rbp)
   2e00c:	movzwl -0x4e(%rbp),%eax
   2e010:	mov    %al,-0x14(%rbp)
   2e013:	movzwl -0x4c(%rbp),%eax
   2e017:	shr    $0x4,%ax
   2e01b:	mov    %al,-0x13(%rbp)
   2e01e:	movzwl -0x4c(%rbp),%eax
   2e022:	shl    $0x4,%eax
   2e025:	mov    %eax,%edx
   2e027:	movzwl -0x4a(%rbp),%eax
   2e02b:	shr    $0x8,%ax
   2e02f:	or     %edx,%eax
   2e031:	mov    %al,-0x12(%rbp)
   2e034:	movzwl -0x4a(%rbp),%eax
   2e038:	mov    %al,-0x11(%rbp)
   2e03b:	mov    -0x20(%rbp),%rax
   2e03f:	mov    -0x18(%rbp),%rdx
   2e043:	mov    -0x8(%rbp),%rcx
   2e047:	sub    %fs:0x28,%rcx
   2e050:	je     2e057 <arx::hw_interface::MotorType2::packMotorMsg(arx::hw_interface::HybridJointCmd*)+0x2a3>
   2e052:	call   10ec0 <__stack_chk_fail@plt>
   2e057:	leave
   2e058:	ret
   2e059:	nop

000000000002e05a <arx::hw_interface::MotorType2::packMotorMsg(double, double, double, double, double)>:
   2e05a:	endbr64
   2e05e:	push   %rbp
   2e05f:	mov    %rsp,%rbp
   2e062:	sub    $0x60,%rsp
   2e066:	mov    %rdi,-0x38(%rbp)
   2e06a:	movsd  %xmm0,-0x40(%rbp)
   2e06f:	movsd  %xmm1,-0x48(%rbp)
   2e074:	movsd  %xmm2,-0x50(%rbp)
   2e079:	movsd  %xmm3,-0x58(%rbp)
   2e07e:	movsd  %xmm4,-0x60(%rbp)
   2e083:	mov    %fs:0x28,%rax
   2e08c:	mov    %rax,-0x8(%rbp)
   2e090:	xor    %eax,%eax
   2e092:	mov    -0x38(%rbp),%rax
   2e096:	movsd  0x6d7a(%rip),%xmm0        # 34e18 <typeinfo name for arx::hw_interface::MotorDlcBase+0x58>
   2e09e:	mov    -0x40(%rbp),%rdx
   2e0a2:	pxor   %xmm2,%xmm2
   2e0a6:	movapd %xmm0,%xmm1
   2e0aa:	movq   %rdx,%xmm0
   2e0af:	mov    %rax,%rdi
   2e0b2:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2e0b7:	movq   %xmm0,%rax
   2e0bc:	mov    %rax,-0x40(%rbp)
   2e0c0:	mov    -0x38(%rbp),%rax
   2e0c4:	movsd  0x6d54(%rip),%xmm0        # 34e20 <typeinfo name for arx::hw_interface::MotorDlcBase+0x60>
   2e0cc:	mov    -0x48(%rbp),%rdx
   2e0d0:	pxor   %xmm2,%xmm2
   2e0d4:	movapd %xmm0,%xmm1
   2e0d8:	movq   %rdx,%xmm0
   2e0dd:	mov    %rax,%rdi
   2e0e0:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2e0e5:	movq   %xmm0,%rax
   2e0ea:	mov    %rax,-0x48(%rbp)
   2e0ee:	mov    -0x38(%rbp),%rax
   2e0f2:	movsd  0x6d06(%rip),%xmm1        # 34e00 <typeinfo name for arx::hw_interface::MotorDlcBase+0x40>
   2e0fa:	movsd  0x6cf6(%rip),%xmm0        # 34df8 <typeinfo name for arx::hw_interface::MotorDlcBase+0x38>
   2e102:	mov    -0x50(%rbp),%rdx
   2e106:	movapd %xmm1,%xmm2
   2e10a:	movapd %xmm0,%xmm1
   2e10e:	movq   %rdx,%xmm0
   2e113:	mov    %rax,%rdi
   2e116:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2e11b:	movq   %xmm0,%rax
   2e120:	mov    %rax,-0x50(%rbp)
   2e124:	mov    -0x38(%rbp),%rax
   2e128:	movsd  0x6cf8(%rip),%xmm1        # 34e28 <typeinfo name for arx::hw_interface::MotorDlcBase+0x68>
   2e130:	movsd  0x6cf8(%rip),%xmm0        # 34e30 <typeinfo name for arx::hw_interface::MotorDlcBase+0x70>
   2e138:	mov    -0x58(%rbp),%rdx
   2e13c:	movapd %xmm1,%xmm2
   2e140:	movapd %xmm0,%xmm1
   2e144:	movq   %rdx,%xmm0
   2e149:	mov    %rax,%rdi
   2e14c:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2e151:	movq   %xmm0,%rax
   2e156:	mov    %rax,-0x58(%rbp)
   2e15a:	mov    -0x38(%rbp),%rax
   2e15e:	movsd  0x6cd2(%rip),%xmm1        # 34e38 <typeinfo name for arx::hw_interface::MotorDlcBase+0x78>
   2e166:	movsd  0x6cd2(%rip),%xmm0        # 34e40 <typeinfo name for arx::hw_interface::MotorDlcBase+0x80>
   2e16e:	mov    -0x60(%rbp),%rdx
   2e172:	movapd %xmm1,%xmm2
   2e176:	movapd %xmm0,%xmm1
   2e17a:	movq   %rdx,%xmm0
   2e17f:	mov    %rax,%rdi
   2e182:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2e187:	movq   %xmm0,%rax
   2e18c:	mov    %rax,-0x60(%rbp)
   2e190:	pxor   %xmm5,%xmm5
   2e194:	cvtsd2ss -0x50(%rbp),%xmm5
   2e199:	movd   %xmm5,%eax
   2e19d:	mov    $0x10,%edi
   2e1a2:	movss  0x6c42(%rip),%xmm2        # 34dec <typeinfo name for arx::hw_interface::MotorDlcBase+0x2c>
   2e1aa:	movss  0x6c3e(%rip),%xmm1        # 34df0 <typeinfo name for arx::hw_interface::MotorDlcBase+0x30>
   2e1b2:	movd   %eax,%xmm0
   2e1b6:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2e1bb:	mov    %ax,-0x2a(%rbp)
   2e1bf:	pxor   %xmm6,%xmm6
   2e1c3:	cvtsd2ss -0x58(%rbp),%xmm6
   2e1c8:	movd   %xmm6,%eax
   2e1cc:	mov    $0xc,%edi
   2e1d1:	movss  0x6c2f(%rip),%xmm2        # 34e08 <typeinfo name for arx::hw_interface::MotorDlcBase+0x48>
   2e1d9:	movss  0x6c2b(%rip),%xmm1        # 34e0c <typeinfo name for arx::hw_interface::MotorDlcBase+0x4c>
   2e1e1:	movd   %eax,%xmm0
   2e1e5:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2e1ea:	mov    %ax,-0x28(%rbp)
   2e1ee:	pxor   %xmm7,%xmm7
   2e1f2:	cvtsd2ss -0x40(%rbp),%xmm7
   2e1f7:	movd   %xmm7,%eax
   2e1fb:	mov    $0xc,%edi
   2e200:	movss  0x6c40(%rip),%xmm2        # 34e48 <typeinfo name for arx::hw_interface::MotorDlcBase+0x88>
   2e208:	pxor   %xmm1,%xmm1
   2e20c:	movd   %eax,%xmm0
   2e210:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2e215:	mov    %ax,-0x26(%rbp)
   2e219:	pxor   %xmm3,%xmm3
   2e21d:	cvtsd2ss -0x48(%rbp),%xmm3
   2e222:	movd   %xmm3,%eax
   2e226:	mov    $0xc,%edi
   2e22b:	movss  0x6c19(%rip),%xmm2        # 34e4c <typeinfo name for arx::hw_interface::MotorDlcBase+0x8c>
   2e233:	pxor   %xmm1,%xmm1
   2e237:	movd   %eax,%xmm0
   2e23b:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2e240:	mov    %ax,-0x24(%rbp)
   2e244:	pxor   %xmm4,%xmm4
   2e248:	cvtsd2ss -0x60(%rbp),%xmm4
   2e24d:	movd   %xmm4,%eax
   2e251:	mov    $0xc,%edi
   2e256:	movss  0x6bb2(%rip),%xmm2        # 34e10 <typeinfo name for arx::hw_interface::MotorDlcBase+0x50>
   2e25e:	movss  0x6bae(%rip),%xmm1        # 34e14 <typeinfo name for arx::hw_interface::MotorDlcBase+0x54>
   2e266:	movd   %eax,%xmm0
   2e26a:	call   2d88f <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2e26f:	mov    %ax,-0x22(%rbp)
   2e273:	movb   $0x8,-0x1c(%rbp)
   2e277:	mov    -0x38(%rbp),%rax
   2e27b:	mov    0x78(%rax),%eax
   2e27e:	mov    %eax,-0x20(%rbp)
   2e281:	movzwl -0x2a(%rbp),%eax
   2e285:	shr    $0x8,%ax
   2e289:	mov    %al,-0x18(%rbp)
   2e28c:	movzwl -0x2a(%rbp),%eax
   2e290:	mov    %al,-0x17(%rbp)
   2e293:	movzwl -0x28(%rbp),%eax
   2e297:	shr    $0x4,%ax
   2e29b:	mov    %al,-0x16(%rbp)
   2e29e:	movzwl -0x28(%rbp),%eax
   2e2a2:	shl    $0x4,%eax
   2e2a5:	mov    %eax,%edx
   2e2a7:	movzwl -0x26(%rbp),%eax
   2e2ab:	shr    $0x8,%ax
   2e2af:	or     %edx,%eax
   2e2b1:	mov    %al,-0x15(%rbp)
   2e2b4:	movzwl -0x26(%rbp),%eax
   2e2b8:	mov    %al,-0x14(%rbp)
   2e2bb:	movzwl -0x24(%rbp),%eax
   2e2bf:	shr    $0x4,%ax
   2e2c3:	mov    %al,-0x13(%rbp)
   2e2c6:	movzwl -0x24(%rbp),%eax
   2e2ca:	shl    $0x4,%eax
   2e2cd:	mov    %eax,%edx
   2e2cf:	movzwl -0x22(%rbp),%eax
   2e2d3:	shr    $0x8,%ax
   2e2d7:	or     %edx,%eax
   2e2d9:	mov    %al,-0x12(%rbp)
   2e2dc:	movzwl -0x22(%rbp),%eax
   2e2e0:	mov    %al,-0x11(%rbp)
   2e2e3:	mov    -0x20(%rbp),%rax
   2e2e7:	mov    -0x18(%rbp),%rdx
   2e2eb:	mov    -0x8(%rbp),%rcx
   2e2ef:	sub    %fs:0x28,%rcx
   2e2f8:	je     2e2ff <arx::hw_interface::MotorType2::packMotorMsg(double, double, double, double, double)+0x2a5>
   2e2fa:	call   10ec0 <__stack_chk_fail@plt>
   2e2ff:	leave
   2e300:	ret
   2e301:	nop

000000000002e302 <arx::hw_interface::MotorType2::packEnableMotor()>:
   2e302:	endbr64
   2e306:	push   %rbp
   2e307:	mov    %rsp,%rbp
   2e30a:	push   %rbx
   2e30b:	sub    $0x38,%rsp
   2e30f:	mov    %rdi,-0x38(%rbp)
   2e313:	mov    %fs:0x28,%rax
   2e31c:	mov    %rax,-0x18(%rbp)
   2e320:	xor    %eax,%eax
   2e322:	mov    -0x38(%rbp),%rbx
   2e326:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   2e32b:	mov    %rax,0x68(%rbx)
   2e32f:	movb   $0x8,-0x2c(%rbp)
   2e333:	mov    -0x38(%rbp),%rax
   2e337:	mov    0x78(%rax),%eax
   2e33a:	mov    %eax,-0x30(%rbp)
   2e33d:	movb   $0xff,-0x28(%rbp)
   2e341:	movb   $0xff,-0x27(%rbp)
   2e345:	movb   $0xff,-0x26(%rbp)
   2e349:	movb   $0xff,-0x25(%rbp)
   2e34d:	movb   $0xff,-0x24(%rbp)
   2e351:	movb   $0xff,-0x23(%rbp)
   2e355:	movb   $0xff,-0x22(%rbp)
   2e359:	movb   $0xfc,-0x21(%rbp)
   2e35d:	mov    -0x30(%rbp),%rax
   2e361:	mov    -0x28(%rbp),%rdx
   2e365:	mov    -0x18(%rbp),%rcx
   2e369:	sub    %fs:0x28,%rcx
   2e372:	je     2e379 <arx::hw_interface::MotorType2::packEnableMotor()+0x77>
   2e374:	call   10ec0 <__stack_chk_fail@plt>
   2e379:	mov    -0x8(%rbp),%rbx
   2e37d:	leave
   2e37e:	ret
   2e37f:	nop

000000000002e380 <arx::hw_interface::MotorType2::packDisableMotor()>:
   2e380:	endbr64
   2e384:	push   %rbp
   2e385:	mov    %rsp,%rbp
   2e388:	sub    $0x30,%rsp
   2e38c:	mov    %rdi,-0x28(%rbp)
   2e390:	mov    %fs:0x28,%rax
   2e399:	mov    %rax,-0x8(%rbp)
   2e39d:	xor    %eax,%eax
   2e39f:	movb   $0x8,-0x1c(%rbp)
   2e3a3:	mov    -0x28(%rbp),%rax
   2e3a7:	mov    0x78(%rax),%eax
   2e3aa:	mov    %eax,-0x20(%rbp)
   2e3ad:	movb   $0xff,-0x18(%rbp)
   2e3b1:	movb   $0xff,-0x17(%rbp)
   2e3b5:	movb   $0xff,-0x16(%rbp)
   2e3b9:	movb   $0xff,-0x15(%rbp)
   2e3bd:	movb   $0xff,-0x14(%rbp)
   2e3c1:	movb   $0xff,-0x13(%rbp)
   2e3c5:	movb   $0xff,-0x12(%rbp)
   2e3c9:	movb   $0xfd,-0x11(%rbp)
   2e3cd:	mov    -0x20(%rbp),%rax
   2e3d1:	mov    -0x18(%rbp),%rdx
   2e3d5:	mov    -0x8(%rbp),%rcx
   2e3d9:	sub    %fs:0x28,%rcx
   2e3e2:	je     2e3e9 <arx::hw_interface::MotorType2::packDisableMotor()+0x69>
   2e3e4:	call   10ec0 <__stack_chk_fail@plt>
   2e3e9:	leave
   2e3ea:	ret
   2e3eb:	nop

000000000002e3ec <arx::hw_interface::MotorType2::packSetZero()>:
   2e3ec:	endbr64
   2e3f0:	push   %rbp
   2e3f1:	mov    %rsp,%rbp
   2e3f4:	sub    $0x30,%rsp
   2e3f8:	mov    %rdi,-0x28(%rbp)
   2e3fc:	mov    %fs:0x28,%rax
   2e405:	mov    %rax,-0x8(%rbp)
   2e409:	xor    %eax,%eax
   2e40b:	movb   $0x8,-0x1c(%rbp)
   2e40f:	mov    -0x28(%rbp),%rax
   2e413:	mov    0x78(%rax),%eax
   2e416:	mov    %eax,-0x20(%rbp)
   2e419:	movb   $0xff,-0x18(%rbp)
   2e41d:	movb   $0xff,-0x17(%rbp)
   2e421:	movb   $0xff,-0x16(%rbp)
   2e425:	movb   $0xff,-0x15(%rbp)
   2e429:	movb   $0xff,-0x14(%rbp)
   2e42d:	movb   $0xff,-0x13(%rbp)
   2e431:	movb   $0xff,-0x12(%rbp)
   2e435:	movb   $0xfe,-0x11(%rbp)
   2e439:	mov    -0x20(%rbp),%rax
   2e43d:	mov    -0x18(%rbp),%rdx
   2e441:	mov    -0x8(%rbp),%rcx
   2e445:	sub    %fs:0x28,%rcx
   2e44e:	je     2e455 <arx::hw_interface::MotorType2::packSetZero()+0x69>
   2e450:	call   10ec0 <__stack_chk_fail@plt>
   2e455:	leave
   2e456:	ret
   2e457:	nop

000000000002e458 <arx::hw_interface::MotorType2::packClearError()>:
   2e458:	endbr64
   2e45c:	push   %rbp
   2e45d:	mov    %rsp,%rbp
   2e460:	sub    $0x30,%rsp
   2e464:	mov    %rdi,-0x28(%rbp)
   2e468:	mov    %fs:0x28,%rax
   2e471:	mov    %rax,-0x8(%rbp)
   2e475:	xor    %eax,%eax
   2e477:	movb   $0x8,-0x1c(%rbp)
   2e47b:	mov    -0x28(%rbp),%rax
   2e47f:	mov    0x78(%rax),%eax
   2e482:	mov    %eax,-0x20(%rbp)
   2e485:	movb   $0xff,-0x18(%rbp)
   2e489:	movb   $0xff,-0x17(%rbp)
   2e48d:	movb   $0xff,-0x16(%rbp)
   2e491:	movb   $0xff,-0x15(%rbp)
   2e495:	movb   $0xff,-0x14(%rbp)
   2e499:	movb   $0xff,-0x13(%rbp)
   2e49d:	movb   $0xff,-0x12(%rbp)
   2e4a1:	movb   $0xfb,-0x11(%rbp)
   2e4a5:	mov    -0x20(%rbp),%rax
   2e4a9:	mov    -0x18(%rbp),%rdx
   2e4ad:	mov    -0x8(%rbp),%rcx
   2e4b1:	sub    %fs:0x28,%rcx
   2e4ba:	je     2e4c1 <arx::hw_interface::MotorType2::packClearError()+0x69>
   2e4bc:	call   10ec0 <__stack_chk_fail@plt>
   2e4c1:	leave
   2e4c2:	ret
   2e4c3:	nop

000000000002e4c4 <arx::hw_interface::MotorType2::resetCircle()>:
   2e4c4:	endbr64
   2e4c8:	push   %rbp
   2e4c9:	mov    %rsp,%rbp
   2e4cc:	mov    %rdi,-0x8(%rbp)
   2e4d0:	mov    -0x8(%rbp),%rax
   2e4d4:	movl   $0x0,0x48(%rax)
   2e4db:	nop
   2e4dc:	pop    %rbp
   2e4dd:	ret

000000000002e4de <arx::hw_interface::HybridJointStatus::HybridJointStatus()>:
   2e4de:	endbr64
   2e4e2:	push   %rbp
   2e4e3:	mov    %rsp,%rbp
   2e4e6:	mov    %rdi,-0x8(%rbp)
   2e4ea:	mov    -0x8(%rbp),%rax
   2e4ee:	pxor   %xmm0,%xmm0
   2e4f2:	movsd  %xmm0,(%rax)
   2e4f6:	mov    -0x8(%rbp),%rax
   2e4fa:	pxor   %xmm0,%xmm0
   2e4fe:	movsd  %xmm0,0x8(%rax)
   2e503:	mov    -0x8(%rbp),%rax
   2e507:	pxor   %xmm0,%xmm0
   2e50b:	movsd  %xmm0,0x10(%rax)
   2e510:	mov    -0x8(%rbp),%rax
   2e514:	pxor   %xmm0,%xmm0
   2e518:	movsd  %xmm0,0x18(%rax)
   2e51d:	nop
   2e51e:	pop    %rbp
   2e51f:	ret

000000000002e520 <arx::hw_interface::MotorDlcBase::~MotorDlcBase()>:
   2e520:	endbr64
   2e524:	push   %rbp
   2e525:	mov    %rsp,%rbp
   2e528:	mov    %rdi,-0x8(%rbp)
   2e52c:	mov    0xda25(%rip),%rax        # 3bf58 <vtable for arx::hw_interface::MotorDlcBase@@Base+0x4b8>
   2e533:	lea    0x10(%rax),%rdx
   2e537:	mov    -0x8(%rbp),%rax
   2e53b:	mov    %rdx,(%rax)
   2e53e:	nop
   2e53f:	pop    %rbp
   2e540:	ret
   2e541:	nop

000000000002e542 <arx::hw_interface::MotorDlcBase::~MotorDlcBase()>:
   2e542:	endbr64
   2e546:	push   %rbp
   2e547:	mov    %rsp,%rbp
   2e54a:	sub    $0x10,%rsp
   2e54e:	mov    %rdi,-0x8(%rbp)
   2e552:	mov    -0x8(%rbp),%rax
   2e556:	mov    %rax,%rdi
   2e559:	call   10520 <arx::hw_interface::MotorDlcBase::~MotorDlcBase()@plt>
   2e55e:	mov    -0x8(%rbp),%rax
   2e562:	mov    $0x10,%esi
   2e567:	mov    %rax,%rdi
   2e56a:	call   10e30 <operator delete(void*, unsigned long)@plt>
   2e56f:	leave
   2e570:	ret
   2e571:	nop

000000000002e572 <arx::hw_interface::MotorDlcBase::getMotorId() const>:
   2e572:	endbr64
   2e576:	push   %rbp
   2e577:	mov    %rsp,%rbp
   2e57a:	mov    %rdi,-0x8(%rbp)
   2e57e:	mov    $0xffffffff,%eax
   2e583:	pop    %rbp
   2e584:	ret
   2e585:	nop

000000000002e586 <arx::hw_interface::MotorDlcBase::packSetZero()>:
   2e586:	endbr64
   2e58a:	push   %rbp
   2e58b:	mov    %rsp,%rbp
   2e58e:	mov    %rdi,-0x8(%rbp)
   2e592:	mov    $0x0,%eax
   2e597:	mov    $0x0,%edx
   2e59c:	pop    %rbp
   2e59d:	ret

000000000002e59e <arx::hw_interface::MotorDlcBase::packClearError()>:
   2e59e:	endbr64
   2e5a2:	push   %rbp
   2e5a3:	mov    %rsp,%rbp
   2e5a6:	mov    %rdi,-0x8(%rbp)
   2e5aa:	mov    $0x0,%eax
   2e5af:	mov    $0x0,%edx
   2e5b4:	pop    %rbp
   2e5b5:	ret

000000000002e5b6 <arx::hw_interface::MotorDlcBase::resetCircle()>:
   2e5b6:	endbr64
   2e5ba:	push   %rbp
   2e5bb:	mov    %rsp,%rbp
   2e5be:	mov    %rdi,-0x8(%rbp)
   2e5c2:	nop
   2e5c3:	pop    %rbp
   2e5c4:	ret
   2e5c5:	nop

000000000002e5c6 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)>:
   2e5c6:	endbr64
   2e5ca:	push   %rbp
   2e5cb:	mov    %rsp,%rbp
   2e5ce:	mov    %rdi,-0x8(%rbp)
   2e5d2:	movsd  %xmm0,-0x10(%rbp)
   2e5d7:	movsd  %xmm1,-0x18(%rbp)
   2e5dc:	movsd  %xmm2,-0x20(%rbp)
   2e5e1:	movsd  -0x10(%rbp),%xmm0
   2e5e6:	comisd -0x18(%rbp),%xmm0
   2e5eb:	jbe    2e5f4 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)+0x2e>
   2e5ed:	movsd  -0x18(%rbp),%xmm0
   2e5f2:	jmp    2e60c <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)+0x46>
   2e5f4:	movsd  -0x20(%rbp),%xmm0
   2e5f9:	comisd -0x10(%rbp),%xmm0
   2e5fe:	jbe    2e607 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)+0x41>
   2e600:	movsd  -0x20(%rbp),%xmm0
   2e605:	jmp    2e60c <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)+0x46>
   2e607:	movsd  -0x10(%rbp),%xmm0
   2e60c:	movq   %xmm0,%rax
   2e611:	movq   %rax,%xmm0
   2e616:	pop    %rbp
   2e617:	ret

000000000002e618 <arx::hw_interface::MotorType2::getMotorId() const>:
   2e618:	endbr64
   2e61c:	push   %rbp
   2e61d:	mov    %rsp,%rbp
   2e620:	mov    %rdi,-0x8(%rbp)
   2e624:	mov    -0x8(%rbp),%rax
   2e628:	mov    0x78(%rax),%eax
   2e62b:	pop    %rbp
   2e62c:	ret
   2e62d:	nop

000000000002e62e <arx::hw_interface::MotorType2::online()>:
   2e62e:	endbr64
   2e632:	push   %rbp
   2e633:	mov    %rsp,%rbp
   2e636:	sub    $0x30,%rsp
   2e63a:	mov    %rdi,-0x28(%rbp)
   2e63e:	mov    %fs:0x28,%rax
   2e647:	mov    %rax,-0x8(%rbp)
   2e64b:	xor    %eax,%eax
   2e64d:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   2e652:	mov    %rax,-0x20(%rbp)
   2e656:	mov    -0x28(%rbp),%rax
   2e65a:	lea    0x30(%rax),%rdx
   2e65e:	lea    -0x20(%rbp),%rax
   2e662:	mov    %rdx,%rsi
   2e665:	mov    %rax,%rdi
   2e668:	call   10a40 <std::common_type<std::chrono::duration<long, std::ratio<1l, 1000000000l> >, std::chrono::duration<long, std::ratio<1l, 1000000000l> > >::type std::chrono::operator-<std::chrono::_V2::system_clock, std::chrono::duration<long, std::ratio<1l, 1000000000l> >, std::chrono::duration<long, std::ratio<1l, 1000000000l> > >(std::chrono::time_point<std::chrono::_V2::system_clock, std::chrono::duration<long, std::ratio<1l, 1000000000l> > > const&, std::chrono::time_point<std::chrono::_V2::system_clock, std::chrono::duration<long, std::ratio<1l, 1000000000l> > > const&)@plt>
   2e66d:	mov    %rax,-0x10(%rbp)
   2e671:	lea    -0x10(%rbp),%rax
   2e675:	mov    %rax,%rdi
   2e678:	call   10600 <std::enable_if<std::chrono::__is_duration<std::chrono::duration<long, std::ratio<1l, 1000000l> > >::value, std::chrono::duration<long, std::ratio<1l, 1000000l> > >::type std::chrono::duration_cast<std::chrono::duration<long, std::ratio<1l, 1000000l> >, long, std::ratio<1l, 1000000000l> >(std::chrono::duration<long, std::ratio<1l, 1000000000l> > const&)@plt>
   2e67d:	mov    %rax,-0x18(%rbp)
   2e681:	lea    -0x18(%rbp),%rax
   2e685:	mov    %rax,%rdi
   2e688:	call   10bc0 <std::chrono::duration<long, std::ratio<1l, 1000000l> >::count() const@plt>
   2e68d:	cmp    $0x30d40,%rax
   2e693:	jle    2e6a8 <arx::hw_interface::MotorType2::online()+0x7a>
   2e695:	mov    -0x28(%rbp),%rax
   2e699:	mov    0x78(%rax),%eax
   2e69c:	cmp    $0x4,%eax
   2e69f:	jg     2e6a8 <arx::hw_interface::MotorType2::online()+0x7a>
   2e6a1:	mov    $0x1,%eax
   2e6a6:	jmp    2e6ad <arx::hw_interface::MotorType2::online()+0x7f>
   2e6a8:	mov    $0x0,%eax
   2e6ad:	test   %al,%al
   2e6af:	je     2e6b9 <arx::hw_interface::MotorType2::online()+0x8b>
   2e6b1:	mov    -0x28(%rbp),%rax
   2e6b5:	movb   $0x0,0x28(%rax)
   2e6b9:	lea    -0x18(%rbp),%rax
   2e6bd:	mov    %rax,%rdi
   2e6c0:	call   10bc0 <std::chrono::duration<long, std::ratio<1l, 1000000l> >::count() const@plt>
   2e6c5:	cmp    $0xc3500,%rax
   2e6cb:	setg   %al
   2e6ce:	test   %al,%al
   2e6d0:	je     2e6da <arx::hw_interface::MotorType2::online()+0xac>
   2e6d2:	mov    -0x28(%rbp),%rax
   2e6d6:	movb   $0x0,0x28(%rax)
   2e6da:	mov    -0x28(%rbp),%rax
   2e6de:	movzbl 0x28(%rax),%eax
   2e6e2:	mov    -0x8(%rbp),%rdx
   2e6e6:	sub    %fs:0x28,%rdx
   2e6ef:	je     2e6f6 <arx::hw_interface::MotorType2::online()+0xc8>
   2e6f1:	call   10ec0 <__stack_chk_fail@plt>
   2e6f6:	leave
   2e6f7:	ret

000000000002e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>:
   2e8ab:	endbr64
   2e8af:	push   %rbp
   2e8b0:	mov    %rsp,%rbp
   2e8b3:	movss  %xmm0,-0x14(%rbp)
   2e8b8:	movss  %xmm1,-0x18(%rbp)
   2e8bd:	movss  %xmm2,-0x1c(%rbp)
   2e8c2:	mov    %edi,-0x20(%rbp)
   2e8c5:	movss  -0x1c(%rbp),%xmm0
   2e8ca:	subss  -0x18(%rbp),%xmm0
   2e8cf:	movss  %xmm0,-0x8(%rbp)
   2e8d4:	movss  -0x18(%rbp),%xmm0
   2e8d9:	movss  %xmm0,-0x4(%rbp)
   2e8de:	movss  -0x14(%rbp),%xmm0
   2e8e3:	movaps %xmm0,%xmm1
   2e8e6:	subss  -0x4(%rbp),%xmm1
   2e8eb:	mov    -0x20(%rbp),%eax
   2e8ee:	mov    $0x1,%edx
   2e8f3:	mov    %eax,%ecx
   2e8f5:	shl    %cl,%edx
   2e8f7:	mov    %edx,%eax
   2e8f9:	sub    $0x1,%eax
   2e8fc:	pxor   %xmm0,%xmm0
   2e900:	cvtsi2ss %eax,%xmm0
   2e904:	mulss  %xmm1,%xmm0
   2e908:	divss  -0x8(%rbp),%xmm0
   2e90d:	cvttss2si %xmm0,%eax
   2e911:	pop    %rbp
   2e912:	ret

000000000002e913 <(anonymous namespace)::uint_to_float(int, float, float, int)>:
   2e913:	endbr64
   2e917:	push   %rbp
   2e918:	mov    %rsp,%rbp
   2e91b:	mov    %edi,-0x14(%rbp)
   2e91e:	movss  %xmm0,-0x18(%rbp)
   2e923:	movss  %xmm1,-0x1c(%rbp)
   2e928:	mov    %esi,-0x20(%rbp)
   2e92b:	movss  -0x1c(%rbp),%xmm0
   2e930:	subss  -0x18(%rbp),%xmm0
   2e935:	movss  %xmm0,-0x8(%rbp)
   2e93a:	movss  -0x18(%rbp),%xmm0
   2e93f:	movss  %xmm0,-0x4(%rbp)
   2e944:	pxor   %xmm0,%xmm0
   2e948:	cvtsi2ssl -0x14(%rbp),%xmm0
   2e94d:	mulss  -0x8(%rbp),%xmm0
   2e952:	mov    -0x20(%rbp),%eax
   2e955:	mov    $0x1,%edx
   2e95a:	mov    %eax,%ecx
   2e95c:	shl    %cl,%edx
   2e95e:	mov    %edx,%eax
   2e960:	sub    $0x1,%eax
   2e963:	pxor   %xmm1,%xmm1
   2e967:	cvtsi2ss %eax,%xmm1
   2e96b:	divss  %xmm1,%xmm0
   2e96f:	addss  -0x4(%rbp),%xmm0
   2e974:	pop    %rbp
   2e975:	ret

000000000002e976 <(anonymous namespace)::int_to_float(int, float, float, int)>:
   2e976:	endbr64
   2e97a:	push   %rbp
   2e97b:	mov    %rsp,%rbp
   2e97e:	mov    %edi,-0x4(%rbp)
   2e981:	movss  %xmm0,-0x8(%rbp)
   2e986:	movss  %xmm1,-0xc(%rbp)
   2e98b:	mov    %esi,-0x10(%rbp)
   2e98e:	pxor   %xmm0,%xmm0
   2e992:	cvtsi2ssl -0x4(%rbp),%xmm0
   2e997:	movss  0x64f1(%rip),%xmm2        # 34e90 <typeinfo name for arx::hw_interface::MotorType4+0x30>
   2e99f:	movaps %xmm0,%xmm1
   2e9a2:	divss  %xmm2,%xmm1
   2e9a6:	movss  -0x8(%rbp),%xmm0
   2e9ab:	subss  -0xc(%rbp),%xmm0
   2e9b0:	mulss  %xmm1,%xmm0
   2e9b4:	addss  -0xc(%rbp),%xmm0
   2e9b9:	pop    %rbp
   2e9ba:	ret

000000000002e9bb <(anonymous namespace)::float32_to_float16(float*, unsigned short*)>:
   2e9bb:	endbr64
   2e9bf:	push   %rbp
   2e9c0:	mov    %rsp,%rbp
   2e9c3:	mov    %rdi,-0x18(%rbp)
   2e9c7:	mov    %rsi,-0x20(%rbp)
   2e9cb:	movw   $0x0,-0x2(%rbp)
   2e9d1:	mov    -0x18(%rbp),%rax
   2e9d5:	movss  (%rax),%xmm0
   2e9d9:	movss  %xmm0,0xe107(%rip)        # 3cae8 <(anonymous namespace)::f32>
   2e9e1:	movzbl 0xe103(%rip),%eax        # 3caeb <(anonymous namespace)::f32+0x3>
   2e9e8:	movzbl %al,%eax
   2e9eb:	add    %eax,%eax
   2e9ed:	movzbl %al,%edx
   2e9f0:	movzbl 0xe0f3(%rip),%eax        # 3caea <(anonymous namespace)::f32+0x2>
   2e9f7:	shr    $0x7,%al
   2e9fa:	movzbl %al,%eax
   2e9fd:	or     %edx,%eax
   2e9ff:	mov    %ax,-0x2(%rbp)
   2ea03:	subw   $0x70,-0x2(%rbp)
   2ea08:	movzwl -0x2(%rbp),%eax
   2ea0c:	shl    $0xa,%eax
   2ea0f:	mov    %eax,%edx
   2ea11:	movzbl 0xe0d2(%rip),%eax        # 3caea <(anonymous namespace)::f32+0x2>
   2ea18:	movzbl %al,%eax
   2ea1b:	shl    $0x3,%eax
   2ea1e:	and    $0x3f8,%ax
   2ea22:	or     %eax,%edx
   2ea24:	movzbl 0xe0be(%rip),%eax        # 3cae9 <(anonymous namespace)::f32+0x1>
   2ea2b:	shr    $0x5,%al
   2ea2e:	movzbl %al,%eax
   2ea31:	or     %edx,%eax
   2ea33:	mov    %eax,%edx
   2ea35:	mov    -0x20(%rbp),%rax
   2ea39:	mov    %dx,(%rax)
   2ea3c:	mov    -0x20(%rbp),%rax
   2ea40:	movzwl (%rax),%edx
   2ea43:	mov    0xe09f(%rip),%eax        # 3cae8 <(anonymous namespace)::f32>
   2ea49:	shr    $0x10,%eax
   2ea4c:	and    $0x8000,%ax
   2ea50:	or     %eax,%edx
   2ea52:	mov    -0x20(%rbp),%rax
   2ea56:	mov    %dx,(%rax)
   2ea59:	nop
   2ea5a:	pop    %rbp
   2ea5b:	ret

000000000002ea5c <(anonymous namespace)::float16_to_float32(unsigned short*, float*)>:
   2ea5c:	endbr64
   2ea60:	push   %rbp
   2ea61:	mov    %rsp,%rbp
   2ea64:	mov    %rdi,-0x18(%rbp)
   2ea68:	mov    %rsi,-0x20(%rbp)
   2ea6c:	movw   $0x0,-0x2(%rbp)
   2ea72:	movl   $0x0,0xe06c(%rip)        # 3cae8 <(anonymous namespace)::f32>
   2ea7c:	mov    -0x18(%rbp),%rax
   2ea80:	movzwl (%rax),%eax
   2ea83:	shr    $0xa,%ax
   2ea87:	and    $0x1f,%eax
   2ea8a:	add    $0x70,%eax
   2ea8d:	mov    %ax,-0x2(%rbp)
   2ea91:	movzwl -0x2(%rbp),%eax
   2ea95:	shr    $1,%ax
   2ea98:	mov    %al,0xe04d(%rip)        # 3caeb <(anonymous namespace)::f32+0x3>
   2ea9e:	movzwl -0x2(%rbp),%eax
   2eaa2:	shl    $0x7,%eax
   2eaa5:	mov    %eax,%edx
   2eaa7:	mov    -0x18(%rbp),%rax
   2eaab:	movzwl (%rax),%eax
   2eaae:	shr    $0x3,%ax
   2eab2:	and    $0x7f,%eax
   2eab5:	or     %edx,%eax
   2eab7:	mov    %al,0xe02d(%rip)        # 3caea <(anonymous namespace)::f32+0x2>
   2eabd:	mov    -0x18(%rbp),%rax
   2eac1:	movzwl (%rax),%eax
   2eac4:	movzwl %ax,%eax
   2eac7:	shl    $0x6,%eax
   2eaca:	mov    %al,0xe019(%rip)        # 3cae9 <(anonymous namespace)::f32+0x1>
   2ead0:	mov    0xe012(%rip),%edx        # 3cae8 <(anonymous namespace)::f32>
   2ead6:	mov    -0x18(%rbp),%rax
   2eada:	movzwl (%rax),%eax
   2eadd:	movzwl %ax,%eax
   2eae0:	shl    $0x10,%eax
   2eae3:	and    $0x80000000,%eax
   2eae8:	or     %edx,%eax
   2eaea:	mov    %eax,0xdff8(%rip)        # 3cae8 <(anonymous namespace)::f32>
   2eaf0:	movss  0xdff0(%rip),%xmm0        # 3cae8 <(anonymous namespace)::f32>
   2eaf8:	mov    -0x20(%rbp),%rax
   2eafc:	movss  %xmm0,(%rax)
   2eb00:	nop
   2eb01:	pop    %rbp
   2eb02:	ret
   2eb03:	nop

000000000002eb04 <arx::hw_interface::MotorType4::CanAnalyze(arx::hw_interface::CanFrame*)>:
   2eb04:	endbr64
   2eb08:	push   %rbp
   2eb09:	mov    %rsp,%rbp
   2eb0c:	push   %rbx
   2eb0d:	sub    $0x38,%rsp
   2eb11:	mov    %rdi,-0x38(%rbp)
   2eb15:	mov    %rsi,-0x40(%rbp)
   2eb19:	movb   $0x0,-0x25(%rbp)
   2eb1d:	mov    -0x40(%rbp),%rax
   2eb21:	mov    (%rax),%edx
   2eb23:	mov    -0x38(%rbp),%rax
   2eb27:	mov    0xa0(%rax),%eax
   2eb2d:	cmp    %eax,%edx
   2eb2f:	jne    2edb0 <arx::hw_interface::MotorType4::CanAnalyze(arx::hw_interface::CanFrame*)+0x2ac>
   2eb35:	mov    -0x40(%rbp),%rax
   2eb39:	movzbl 0x9(%rax),%eax
   2eb3d:	movzbl %al,%eax
   2eb40:	shl    $0x8,%eax
   2eb43:	mov    %eax,%edx
   2eb45:	mov    -0x40(%rbp),%rax
   2eb49:	movzbl 0xa(%rax),%eax
   2eb4d:	movzbl %al,%eax
   2eb50:	or     %edx,%eax
   2eb52:	mov    %eax,-0x24(%rbp)
   2eb55:	mov    -0x40(%rbp),%rax
   2eb59:	movzbl 0xb(%rax),%eax
   2eb5d:	movzbl %al,%eax
   2eb60:	shl    $0x4,%eax
   2eb63:	mov    %eax,%edx
   2eb65:	mov    -0x40(%rbp),%rax
   2eb69:	movzbl 0xc(%rax),%eax
   2eb6d:	shr    $0x4,%al
   2eb70:	movzbl %al,%eax
   2eb73:	or     %edx,%eax
   2eb75:	mov    %eax,-0x20(%rbp)
   2eb78:	mov    -0x40(%rbp),%rax
   2eb7c:	movzbl 0xc(%rax),%eax
   2eb80:	movzbl %al,%eax
   2eb83:	shl    $0x8,%eax
   2eb86:	and    $0xf00,%eax
   2eb8b:	mov    %eax,%edx
   2eb8d:	mov    -0x40(%rbp),%rax
   2eb91:	movzbl 0xd(%rax),%eax
   2eb95:	movzbl %al,%eax
   2eb98:	or     %edx,%eax
   2eb9a:	mov    %eax,-0x1c(%rbp)
   2eb9d:	mov    -0x40(%rbp),%rax
   2eba1:	movzbl 0x8(%rax),%eax
   2eba5:	movzbl %al,%eax
   2eba8:	and    $0x1f,%eax
   2ebab:	mov    %eax,%edx
   2ebad:	mov    -0x38(%rbp),%rax
   2ebb1:	mov    %edx,0x60(%rax)
   2ebb4:	mov    -0x24(%rbp),%eax
   2ebb7:	mov    $0x10,%esi
   2ebbc:	movss  0x62d0(%rip),%xmm1        # 34e94 <typeinfo name for arx::hw_interface::MotorType4+0x34>
   2ebc4:	mov    0x62ce(%rip),%edx        # 34e98 <typeinfo name for arx::hw_interface::MotorType4+0x38>
   2ebca:	movd   %edx,%xmm0
   2ebce:	mov    %eax,%edi
   2ebd0:	call   2e913 <(anonymous namespace)::uint_to_float(int, float, float, int)>
   2ebd5:	cvtss2sd %xmm0,%xmm0
   2ebd9:	movsd  %xmm0,-0x18(%rbp)
   2ebde:	mov    -0x38(%rbp),%rax
   2ebe2:	movsd  0x40(%rax),%xmm1
   2ebe7:	movsd  -0x18(%rbp),%xmm0
   2ebec:	subsd  %xmm1,%xmm0
   2ebf0:	comisd 0x62a8(%rip),%xmm0        # 34ea0 <typeinfo name for arx::hw_interface::MotorType4+0x40>
   2ebf8:	jbe    2ec0d <arx::hw_interface::MotorType4::CanAnalyze(arx::hw_interface::CanFrame*)+0x109>
   2ebfa:	mov    -0x38(%rbp),%rax
   2ebfe:	mov    0x48(%rax),%eax
   2ec01:	lea    -0x1(%rax),%edx
   2ec04:	mov    -0x38(%rbp),%rax
   2ec08:	mov    %edx,0x48(%rax)
   2ec0b:	jmp    2ec42 <arx::hw_interface::MotorType4::CanAnalyze(arx::hw_interface::CanFrame*)+0x13e>
   2ec0d:	mov    -0x38(%rbp),%rax
   2ec11:	movsd  0x40(%rax),%xmm2
   2ec16:	movsd  -0x18(%rbp),%xmm0
   2ec1b:	movapd %xmm0,%xmm1
   2ec1f:	subsd  %xmm2,%xmm1
   2ec23:	movsd  0x627d(%rip),%xmm0        # 34ea8 <typeinfo name for arx::hw_interface::MotorType4+0x48>
   2ec2b:	comisd %xmm1,%xmm0
   2ec2f:	jbe    2ec42 <arx::hw_interface::MotorType4::CanAnalyze(arx::hw_interface::CanFrame*)+0x13e>
   2ec31:	mov    -0x38(%rbp),%rax
   2ec35:	mov    0x48(%rax),%eax
   2ec38:	lea    0x1(%rax),%edx
   2ec3b:	mov    -0x38(%rbp),%rax
   2ec3f:	mov    %edx,0x48(%rax)
   2ec42:	mov    -0x38(%rbp),%rax
   2ec46:	movsd  -0x18(%rbp),%xmm0
   2ec4b:	movsd  %xmm0,0x40(%rax)
   2ec50:	mov    -0x38(%rbp),%rbx
   2ec54:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   2ec59:	mov    %rax,0x70(%rbx)
   2ec5d:	mov    -0x38(%rbp),%rax
   2ec61:	mov    0x48(%rax),%eax
   2ec64:	pxor   %xmm0,%xmm0
   2ec68:	cvtsi2sd %eax,%xmm0
   2ec6c:	movapd %xmm0,%xmm1
   2ec70:	addsd  %xmm0,%xmm1
   2ec74:	movsd  0x6224(%rip),%xmm0        # 34ea0 <typeinfo name for arx::hw_interface::MotorType4+0x40>
   2ec7c:	mulsd  %xmm1,%xmm0
   2ec80:	movapd %xmm0,%xmm1
   2ec84:	addsd  -0x18(%rbp),%xmm1
   2ec89:	mov    -0x38(%rbp),%rax
   2ec8d:	movsd  0x80(%rax),%xmm0
   2ec95:	addsd  %xmm1,%xmm0
   2ec99:	mov    -0x38(%rbp),%rax
   2ec9d:	movsd  %xmm0,0x38(%rax)
   2eca2:	mov    -0x38(%rbp),%rax
   2eca6:	movsd  0x38(%rax),%xmm0
   2ecab:	mov    -0x38(%rbp),%rax
   2ecaf:	movsd  0x90(%rax),%xmm1
   2ecb7:	comisd %xmm1,%xmm0
   2ecbb:	jbe    2ece8 <arx::hw_interface::MotorType4::CanAnalyze(arx::hw_interface::CanFrame*)+0x1e4>
   2ecbd:	mov    -0x38(%rbp),%rax
   2ecc1:	movsd  0x38(%rax),%xmm0
   2ecc6:	movsd  0x61e2(%rip),%xmm1        # 34eb0 <typeinfo name for arx::hw_interface::MotorType4+0x50>
   2ecce:	subsd  %xmm1,%xmm0
   2ecd2:	mov    -0x38(%rbp),%rax
   2ecd6:	movsd  %xmm0,0x38(%rax)
   2ecdb:	mov    -0x38(%rbp),%rax
   2ecdf:	movl   $0x1,0x78(%rax)
   2ece6:	jmp    2ed2c <arx::hw_interface::MotorType4::CanAnalyze(arx::hw_interface::CanFrame*)+0x228>
   2ece8:	mov    -0x38(%rbp),%rax
   2ecec:	movsd  0x38(%rax),%xmm1
   2ecf1:	mov    -0x38(%rbp),%rax
   2ecf5:	movsd  0x88(%rax),%xmm0
   2ecfd:	comisd %xmm1,%xmm0
   2ed01:	jbe    2ed2c <arx::hw_interface::MotorType4::CanAnalyze(arx::hw_interface::CanFrame*)+0x228>
   2ed03:	mov    -0x38(%rbp),%rax
   2ed07:	movsd  0x38(%rax),%xmm1
   2ed0c:	movsd  0x619c(%rip),%xmm0        # 34eb0 <typeinfo name for arx::hw_interface::MotorType4+0x50>
   2ed14:	addsd  %xmm1,%xmm0
   2ed18:	mov    -0x38(%rbp),%rax
   2ed1c:	movsd  %xmm0,0x38(%rax)
   2ed21:	mov    -0x38(%rbp),%rax
   2ed25:	movl   $0xffffffff,0x78(%rax)
   2ed2c:	mov    -0x20(%rbp),%eax
   2ed2f:	mov    $0xc,%esi
   2ed34:	movss  0x617c(%rip),%xmm1        # 34eb8 <typeinfo name for arx::hw_interface::MotorType4+0x58>
   2ed3c:	mov    0x617a(%rip),%edx        # 34ebc <typeinfo name for arx::hw_interface::MotorType4+0x5c>
   2ed42:	movd   %edx,%xmm0
   2ed46:	mov    %eax,%edi
   2ed48:	call   2e913 <(anonymous namespace)::uint_to_float(int, float, float, int)>
   2ed4d:	cvtss2sd %xmm0,%xmm0
   2ed51:	mov    -0x38(%rbp),%rax
   2ed55:	movsd  %xmm0,0x50(%rax)
   2ed5a:	mov    -0x1c(%rbp),%eax
   2ed5d:	mov    $0xc,%esi
   2ed62:	movss  0x6156(%rip),%xmm1        # 34ec0 <typeinfo name for arx::hw_interface::MotorType4+0x60>
   2ed6a:	mov    0x6154(%rip),%edx        # 34ec4 <typeinfo name for arx::hw_interface::MotorType4+0x64>
   2ed70:	movd   %edx,%xmm0
   2ed74:	mov    %eax,%edi
   2ed76:	call   2e913 <(anonymous namespace)::uint_to_float(int, float, float, int)>
   2ed7b:	cvtss2sd %xmm0,%xmm0
   2ed7f:	mov    -0x38(%rbp),%rax
   2ed83:	movsd  %xmm0,0x58(%rax)
   2ed88:	mov    -0x40(%rbp),%rax
   2ed8c:	movzbl 0xe(%rax),%eax
   2ed90:	movzbl %al,%eax
   2ed93:	sub    $0x32,%eax
   2ed96:	mov    %eax,%edx
   2ed98:	shr    $0x1f,%edx
   2ed9b:	add    %edx,%eax
   2ed9d:	sar    $1,%eax
   2ed9f:	pxor   %xmm0,%xmm0
   2eda3:	cvtsi2sd %eax,%xmm0
   2eda7:	mov    -0x38(%rbp),%rax
   2edab:	movsd  %xmm0,0x68(%rax)
   2edb0:	nop
   2edb1:	mov    -0x8(%rbp),%rbx
   2edb5:	leave
   2edb6:	ret
   2edb7:	nop

000000000002edb8 <arx::hw_interface::MotorType4::GetMotorMsg()>:
   2edb8:	endbr64
   2edbc:	push   %rbp
   2edbd:	mov    %rsp,%rbp
   2edc0:	sub    $0x10,%rsp
   2edc4:	mov    %rdi,-0x8(%rbp)
   2edc8:	mov    %rsi,-0x10(%rbp)
   2edcc:	mov    -0x8(%rbp),%rax
   2edd0:	mov    %rax,%rdi
   2edd3:	call   10500 <arx::hw_interface::HybridJointStatus::HybridJointStatus()@plt>
   2edd8:	mov    -0x10(%rbp),%rax
   2eddc:	movsd  0x10(%rax),%xmm0
   2ede1:	mov    -0x8(%rbp),%rax
   2ede5:	movsd  %xmm0,(%rax)
   2ede9:	mov    -0x10(%rbp),%rax
   2eded:	movsd  0x18(%rax),%xmm0
   2edf2:	mov    -0x8(%rbp),%rax
   2edf6:	movsd  %xmm0,0x8(%rax)
   2edfb:	mov    -0x10(%rbp),%rax
   2edff:	movsd  0x20(%rax),%xmm0
   2ee04:	mov    -0x8(%rbp),%rax
   2ee08:	movsd  %xmm0,0x18(%rax)
   2ee0d:	mov    -0x10(%rbp),%rax
   2ee11:	movsd  0x20(%rax),%xmm0
   2ee16:	mov    -0x8(%rbp),%rax
   2ee1a:	movsd  %xmm0,0x10(%rax)
   2ee1f:	nop
   2ee20:	mov    -0x8(%rbp),%rax
   2ee24:	leave
   2ee25:	ret

000000000002ee26 <arx::hw_interface::MotorType4::ExchangeMotorMsg()>:
   2ee26:	endbr64
   2ee2a:	push   %rbp
   2ee2b:	mov    %rsp,%rbp
   2ee2e:	mov    %rdi,-0x8(%rbp)
   2ee32:	mov    -0x8(%rbp),%rax
   2ee36:	movsd  0x38(%rax),%xmm0
   2ee3b:	mov    -0x8(%rbp),%rax
   2ee3f:	movsd  %xmm0,0x10(%rax)
   2ee44:	mov    -0x8(%rbp),%rax
   2ee48:	movsd  0x50(%rax),%xmm0
   2ee4d:	mov    -0x8(%rbp),%rax
   2ee51:	movsd  %xmm0,0x18(%rax)
   2ee56:	mov    -0x8(%rbp),%rax
   2ee5a:	movsd  0x58(%rax),%xmm0
   2ee5f:	mov    -0x8(%rbp),%rax
   2ee63:	movsd  %xmm0,0x20(%rax)
   2ee68:	mov    -0x8(%rbp),%rax
   2ee6c:	mov    0x60(%rax),%edx
   2ee6f:	mov    -0x8(%rbp),%rax
   2ee73:	mov    %edx,0x8(%rax)
   2ee76:	mov    -0x8(%rbp),%rax
   2ee7a:	mov    -0x8(%rbp),%rdx
   2ee7e:	mov    0x70(%rdx),%rdx
   2ee82:	mov    %rdx,0x30(%rax)
   2ee86:	nop
   2ee87:	pop    %rbp
   2ee88:	ret
   2ee89:	nop

000000000002ee8a <arx::hw_interface::MotorType4::packMotorMsg(arx::hw_interface::HybridJointCmd*)>:
   2ee8a:	endbr64
   2ee8e:	push   %rbp
   2ee8f:	mov    %rsp,%rbp
   2ee92:	sub    $0x70,%rsp
   2ee96:	mov    %rdi,-0x68(%rbp)
   2ee9a:	mov    %rsi,-0x70(%rbp)
   2ee9e:	mov    %fs:0x28,%rax
   2eea7:	mov    %rax,-0x8(%rbp)
   2eeab:	xor    %eax,%eax
   2eead:	mov    -0x68(%rbp),%rax
   2eeb1:	mov    -0x70(%rbp),%rdx
   2eeb5:	mov    0x18(%rdx),%rdx
   2eeb9:	movsd  0x6007(%rip),%xmm0        # 34ec8 <typeinfo name for arx::hw_interface::MotorType4+0x68>
   2eec1:	pxor   %xmm2,%xmm2
   2eec5:	movapd %xmm0,%xmm1
   2eec9:	movq   %rdx,%xmm0
   2eece:	mov    %rax,%rdi
   2eed1:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2eed6:	movq   %xmm0,%rax
   2eedb:	mov    %rax,-0x48(%rbp)
   2eedf:	mov    -0x68(%rbp),%rax
   2eee3:	mov    -0x70(%rbp),%rdx
   2eee7:	mov    0x20(%rdx),%rdx
   2eeeb:	movsd  0x5fdd(%rip),%xmm0        # 34ed0 <typeinfo name for arx::hw_interface::MotorType4+0x70>
   2eef3:	pxor   %xmm2,%xmm2
   2eef7:	movapd %xmm0,%xmm1
   2eefb:	movq   %rdx,%xmm0
   2ef00:	mov    %rax,%rdi
   2ef03:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2ef08:	movq   %xmm0,%rax
   2ef0d:	mov    %rax,-0x40(%rbp)
   2ef11:	mov    -0x68(%rbp),%rax
   2ef15:	mov    -0x70(%rbp),%rdx
   2ef19:	movsd  (%rdx),%xmm0
   2ef1d:	mov    -0x68(%rbp),%rdx
   2ef21:	movsd  0x80(%rdx),%xmm2
   2ef29:	movapd %xmm0,%xmm1
   2ef2d:	subsd  %xmm2,%xmm1
   2ef31:	mov    -0x68(%rbp),%rdx
   2ef35:	mov    0x78(%rdx),%edx
   2ef38:	add    %edx,%edx
   2ef3a:	pxor   %xmm2,%xmm2
   2ef3e:	cvtsi2sd %edx,%xmm2
   2ef42:	movsd  0x5f8e(%rip),%xmm0        # 34ed8 <typeinfo name for arx::hw_interface::MotorType4+0x78>
   2ef4a:	mulsd  %xmm2,%xmm0
   2ef4e:	addsd  %xmm0,%xmm1
   2ef52:	movq   %xmm1,%rdx
   2ef57:	movsd  0x5f49(%rip),%xmm1        # 34ea8 <typeinfo name for arx::hw_interface::MotorType4+0x48>
   2ef5f:	movsd  0x5f39(%rip),%xmm0        # 34ea0 <typeinfo name for arx::hw_interface::MotorType4+0x40>
   2ef67:	movapd %xmm1,%xmm2
   2ef6b:	movapd %xmm0,%xmm1
   2ef6f:	movq   %rdx,%xmm0
   2ef74:	mov    %rax,%rdi
   2ef77:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2ef7c:	movq   %xmm0,%rax
   2ef81:	mov    %rax,-0x38(%rbp)
   2ef85:	mov    -0x68(%rbp),%rax
   2ef89:	mov    -0x70(%rbp),%rdx
   2ef8d:	mov    0x8(%rdx),%rdx
   2ef91:	movsd  0x5f47(%rip),%xmm1        # 34ee0 <typeinfo name for arx::hw_interface::MotorType4+0x80>
   2ef99:	movsd  0x5f47(%rip),%xmm0        # 34ee8 <typeinfo name for arx::hw_interface::MotorType4+0x88>
   2efa1:	movapd %xmm1,%xmm2
   2efa5:	movapd %xmm0,%xmm1
   2efa9:	movq   %rdx,%xmm0
   2efae:	mov    %rax,%rdi
   2efb1:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2efb6:	movq   %xmm0,%rax
   2efbb:	mov    %rax,-0x30(%rbp)
   2efbf:	mov    -0x68(%rbp),%rax
   2efc3:	mov    -0x70(%rbp),%rdx
   2efc7:	mov    0x10(%rdx),%rdx
   2efcb:	movsd  0x5f1d(%rip),%xmm1        # 34ef0 <typeinfo name for arx::hw_interface::MotorType4+0x90>
   2efd3:	movsd  0x5f1d(%rip),%xmm0        # 34ef8 <typeinfo name for arx::hw_interface::MotorType4+0x98>
   2efdb:	movapd %xmm1,%xmm2
   2efdf:	movapd %xmm0,%xmm1
   2efe3:	movq   %rdx,%xmm0
   2efe8:	mov    %rax,%rdi
   2efeb:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2eff0:	movq   %xmm0,%rax
   2eff5:	mov    %rax,-0x28(%rbp)
   2eff9:	pxor   %xmm3,%xmm3
   2effd:	cvtsd2ss -0x38(%rbp),%xmm3
   2f002:	movd   %xmm3,%eax
   2f006:	mov    $0x10,%edi
   2f00b:	movss  0x5e81(%rip),%xmm2        # 34e94 <typeinfo name for arx::hw_interface::MotorType4+0x34>
   2f013:	movss  0x5e7d(%rip),%xmm1        # 34e98 <typeinfo name for arx::hw_interface::MotorType4+0x38>
   2f01b:	movd   %eax,%xmm0
   2f01f:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f024:	mov    %ax,-0x52(%rbp)
   2f028:	pxor   %xmm4,%xmm4
   2f02c:	cvtsd2ss -0x30(%rbp),%xmm4
   2f031:	movd   %xmm4,%eax
   2f035:	mov    $0xc,%edi
   2f03a:	movss  0x5e76(%rip),%xmm2        # 34eb8 <typeinfo name for arx::hw_interface::MotorType4+0x58>
   2f042:	movss  0x5e72(%rip),%xmm1        # 34ebc <typeinfo name for arx::hw_interface::MotorType4+0x5c>
   2f04a:	movd   %eax,%xmm0
   2f04e:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f053:	mov    %ax,-0x50(%rbp)
   2f057:	pxor   %xmm5,%xmm5
   2f05b:	cvtsd2ss -0x48(%rbp),%xmm5
   2f060:	movd   %xmm5,%eax
   2f064:	mov    $0xc,%edi
   2f069:	movss  0x5e8f(%rip),%xmm2        # 34f00 <typeinfo name for arx::hw_interface::MotorType4+0xa0>
   2f071:	pxor   %xmm1,%xmm1
   2f075:	movd   %eax,%xmm0
   2f079:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f07e:	mov    %ax,-0x4e(%rbp)
   2f082:	pxor   %xmm6,%xmm6
   2f086:	cvtsd2ss -0x40(%rbp),%xmm6
   2f08b:	movd   %xmm6,%eax
   2f08f:	mov    $0xc,%edi
   2f094:	movss  0x5e68(%rip),%xmm2        # 34f04 <typeinfo name for arx::hw_interface::MotorType4+0xa4>
   2f09c:	pxor   %xmm1,%xmm1
   2f0a0:	movd   %eax,%xmm0
   2f0a4:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f0a9:	mov    %ax,-0x4c(%rbp)
   2f0ad:	pxor   %xmm7,%xmm7
   2f0b1:	cvtsd2ss -0x28(%rbp),%xmm7
   2f0b6:	movd   %xmm7,%eax
   2f0ba:	mov    $0xc,%edi
   2f0bf:	movss  0x5df9(%rip),%xmm2        # 34ec0 <typeinfo name for arx::hw_interface::MotorType4+0x60>
   2f0c7:	movss  0x5df5(%rip),%xmm1        # 34ec4 <typeinfo name for arx::hw_interface::MotorType4+0x64>
   2f0cf:	movd   %eax,%xmm0
   2f0d3:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f0d8:	mov    %ax,-0x4a(%rbp)
   2f0dc:	movb   $0x8,-0x1c(%rbp)
   2f0e0:	mov    -0x68(%rbp),%rax
   2f0e4:	mov    0xa0(%rax),%eax
   2f0ea:	mov    %eax,-0x20(%rbp)
   2f0ed:	movzwl -0x4e(%rbp),%eax
   2f0f1:	shr    $0x7,%ax
   2f0f5:	mov    %al,-0x18(%rbp)
   2f0f8:	movzwl -0x4e(%rbp),%eax
   2f0fc:	add    %eax,%eax
   2f0fe:	mov    %eax,%edx
   2f100:	movzwl -0x4c(%rbp),%eax
   2f104:	shr    $0x8,%ax
   2f108:	and    $0x1,%eax
   2f10b:	or     %edx,%eax
   2f10d:	mov    %al,-0x17(%rbp)
   2f110:	movzwl -0x4c(%rbp),%eax
   2f114:	mov    %al,-0x16(%rbp)
   2f117:	movzwl -0x52(%rbp),%eax
   2f11b:	shr    $0x8,%ax
   2f11f:	mov    %al,-0x15(%rbp)
   2f122:	movzwl -0x52(%rbp),%eax
   2f126:	mov    %al,-0x14(%rbp)
   2f129:	movzwl -0x50(%rbp),%eax
   2f12d:	shr    $0x4,%ax
   2f131:	mov    %al,-0x13(%rbp)
   2f134:	movzwl -0x50(%rbp),%eax
   2f138:	shl    $0x4,%eax
   2f13b:	mov    %eax,%edx
   2f13d:	movzwl -0x4a(%rbp),%eax
   2f141:	shr    $0x8,%ax
   2f145:	or     %edx,%eax
   2f147:	mov    %al,-0x12(%rbp)
   2f14a:	movzwl -0x4a(%rbp),%eax
   2f14e:	mov    %al,-0x11(%rbp)
   2f151:	mov    -0x20(%rbp),%rax
   2f155:	mov    -0x18(%rbp),%rdx
   2f159:	mov    -0x8(%rbp),%rcx
   2f15d:	sub    %fs:0x28,%rcx
   2f166:	je     2f16d <arx::hw_interface::MotorType4::packMotorMsg(arx::hw_interface::HybridJointCmd*)+0x2e3>
   2f168:	call   10ec0 <__stack_chk_fail@plt>
   2f16d:	leave
   2f16e:	ret
   2f16f:	nop

000000000002f170 <arx::hw_interface::MotorType4::packMotorMsg(double, double, double, double, double)>:
   2f170:	endbr64
   2f174:	push   %rbp
   2f175:	mov    %rsp,%rbp
   2f178:	sub    $0x60,%rsp
   2f17c:	mov    %rdi,-0x38(%rbp)
   2f180:	movsd  %xmm0,-0x40(%rbp)
   2f185:	movsd  %xmm1,-0x48(%rbp)
   2f18a:	movsd  %xmm2,-0x50(%rbp)
   2f18f:	movsd  %xmm3,-0x58(%rbp)
   2f194:	movsd  %xmm4,-0x60(%rbp)
   2f199:	mov    %fs:0x28,%rax
   2f1a2:	mov    %rax,-0x8(%rbp)
   2f1a6:	xor    %eax,%eax
   2f1a8:	mov    -0x38(%rbp),%rax
   2f1ac:	movsd  0x5d14(%rip),%xmm0        # 34ec8 <typeinfo name for arx::hw_interface::MotorType4+0x68>
   2f1b4:	mov    -0x40(%rbp),%rdx
   2f1b8:	pxor   %xmm2,%xmm2
   2f1bc:	movapd %xmm0,%xmm1
   2f1c0:	movq   %rdx,%xmm0
   2f1c5:	mov    %rax,%rdi
   2f1c8:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2f1cd:	movq   %xmm0,%rax
   2f1d2:	mov    %rax,-0x40(%rbp)
   2f1d6:	mov    -0x38(%rbp),%rax
   2f1da:	movsd  0x5cee(%rip),%xmm0        # 34ed0 <typeinfo name for arx::hw_interface::MotorType4+0x70>
   2f1e2:	mov    -0x48(%rbp),%rdx
   2f1e6:	pxor   %xmm2,%xmm2
   2f1ea:	movapd %xmm0,%xmm1
   2f1ee:	movq   %rdx,%xmm0
   2f1f3:	mov    %rax,%rdi
   2f1f6:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2f1fb:	movq   %xmm0,%rax
   2f200:	mov    %rax,-0x48(%rbp)
   2f204:	mov    -0x38(%rbp),%rax
   2f208:	mov    -0x38(%rbp),%rdx
   2f20c:	movsd  0x80(%rdx),%xmm2
   2f214:	movsd  -0x50(%rbp),%xmm0
   2f219:	movapd %xmm0,%xmm1
   2f21d:	subsd  %xmm2,%xmm1
   2f221:	mov    -0x38(%rbp),%rdx
   2f225:	mov    0x78(%rdx),%edx
   2f228:	add    %edx,%edx
   2f22a:	pxor   %xmm2,%xmm2
   2f22e:	cvtsi2sd %edx,%xmm2
   2f232:	movsd  0x5c9e(%rip),%xmm0        # 34ed8 <typeinfo name for arx::hw_interface::MotorType4+0x78>
   2f23a:	mulsd  %xmm2,%xmm0
   2f23e:	addsd  %xmm0,%xmm1
   2f242:	movq   %xmm1,%rdx
   2f247:	movsd  0x5c59(%rip),%xmm1        # 34ea8 <typeinfo name for arx::hw_interface::MotorType4+0x48>
   2f24f:	movsd  0x5c49(%rip),%xmm0        # 34ea0 <typeinfo name for arx::hw_interface::MotorType4+0x40>
   2f257:	movapd %xmm1,%xmm2
   2f25b:	movapd %xmm0,%xmm1
   2f25f:	movq   %rdx,%xmm0
   2f264:	mov    %rax,%rdi
   2f267:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2f26c:	movq   %xmm0,%rax
   2f271:	mov    %rax,-0x50(%rbp)
   2f275:	mov    -0x38(%rbp),%rax
   2f279:	movsd  0x5c5f(%rip),%xmm1        # 34ee0 <typeinfo name for arx::hw_interface::MotorType4+0x80>
   2f281:	movsd  0x5c5f(%rip),%xmm0        # 34ee8 <typeinfo name for arx::hw_interface::MotorType4+0x88>
   2f289:	mov    -0x58(%rbp),%rdx
   2f28d:	movapd %xmm1,%xmm2
   2f291:	movapd %xmm0,%xmm1
   2f295:	movq   %rdx,%xmm0
   2f29a:	mov    %rax,%rdi
   2f29d:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2f2a2:	movq   %xmm0,%rax
   2f2a7:	mov    %rax,-0x58(%rbp)
   2f2ab:	mov    -0x38(%rbp),%rax
   2f2af:	movsd  0x5c39(%rip),%xmm1        # 34ef0 <typeinfo name for arx::hw_interface::MotorType4+0x90>
   2f2b7:	movsd  0x5c39(%rip),%xmm0        # 34ef8 <typeinfo name for arx::hw_interface::MotorType4+0x98>
   2f2bf:	mov    -0x60(%rbp),%rdx
   2f2c3:	movapd %xmm1,%xmm2
   2f2c7:	movapd %xmm0,%xmm1
   2f2cb:	movq   %rdx,%xmm0
   2f2d0:	mov    %rax,%rdi
   2f2d3:	call   10570 <arx::hw_interface::MotorDlcBase::restrictBound(double, double, double)@plt>
   2f2d8:	movq   %xmm0,%rax
   2f2dd:	mov    %rax,-0x60(%rbp)
   2f2e1:	pxor   %xmm5,%xmm5
   2f2e5:	cvtsd2ss -0x50(%rbp),%xmm5
   2f2ea:	movd   %xmm5,%eax
   2f2ee:	mov    $0x10,%edi
   2f2f3:	movss  0x5b99(%rip),%xmm2        # 34e94 <typeinfo name for arx::hw_interface::MotorType4+0x34>
   2f2fb:	movss  0x5b95(%rip),%xmm1        # 34e98 <typeinfo name for arx::hw_interface::MotorType4+0x38>
   2f303:	movd   %eax,%xmm0
   2f307:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f30c:	mov    %ax,-0x2a(%rbp)
   2f310:	pxor   %xmm6,%xmm6
   2f314:	cvtsd2ss -0x58(%rbp),%xmm6
   2f319:	movd   %xmm6,%eax
   2f31d:	mov    $0xc,%edi
   2f322:	movss  0x5b8e(%rip),%xmm2        # 34eb8 <typeinfo name for arx::hw_interface::MotorType4+0x58>
   2f32a:	movss  0x5b8a(%rip),%xmm1        # 34ebc <typeinfo name for arx::hw_interface::MotorType4+0x5c>
   2f332:	movd   %eax,%xmm0
   2f336:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f33b:	mov    %ax,-0x28(%rbp)
   2f33f:	pxor   %xmm7,%xmm7
   2f343:	cvtsd2ss -0x40(%rbp),%xmm7
   2f348:	movd   %xmm7,%eax
   2f34c:	mov    $0xc,%edi
   2f351:	movss  0x5ba7(%rip),%xmm2        # 34f00 <typeinfo name for arx::hw_interface::MotorType4+0xa0>
   2f359:	pxor   %xmm1,%xmm1
   2f35d:	movd   %eax,%xmm0
   2f361:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f366:	mov    %ax,-0x26(%rbp)
   2f36a:	pxor   %xmm3,%xmm3
   2f36e:	cvtsd2ss -0x48(%rbp),%xmm3
   2f373:	movd   %xmm3,%eax
   2f377:	mov    $0xc,%edi
   2f37c:	movss  0x5b80(%rip),%xmm2        # 34f04 <typeinfo name for arx::hw_interface::MotorType4+0xa4>
   2f384:	pxor   %xmm1,%xmm1
   2f388:	movd   %eax,%xmm0
   2f38c:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f391:	mov    %ax,-0x24(%rbp)
   2f395:	pxor   %xmm4,%xmm4
   2f399:	cvtsd2ss -0x60(%rbp),%xmm4
   2f39e:	movd   %xmm4,%eax
   2f3a2:	mov    $0xc,%edi
   2f3a7:	movss  0x5b11(%rip),%xmm2        # 34ec0 <typeinfo name for arx::hw_interface::MotorType4+0x60>
   2f3af:	movss  0x5b0d(%rip),%xmm1        # 34ec4 <typeinfo name for arx::hw_interface::MotorType4+0x64>
   2f3b7:	movd   %eax,%xmm0
   2f3bb:	call   2e8ab <(anonymous namespace)::float_to_uint(float, float, float, int)>
   2f3c0:	mov    %ax,-0x22(%rbp)
   2f3c4:	movb   $0x8,-0x1c(%rbp)
   2f3c8:	mov    -0x38(%rbp),%rax
   2f3cc:	mov    0xa0(%rax),%eax
   2f3d2:	mov    %eax,-0x20(%rbp)
   2f3d5:	movzwl -0x26(%rbp),%eax
   2f3d9:	shr    $0x7,%ax
   2f3dd:	mov    %al,-0x18(%rbp)
   2f3e0:	movzwl -0x26(%rbp),%eax
   2f3e4:	add    %eax,%eax
   2f3e6:	mov    %eax,%edx
   2f3e8:	movzwl -0x24(%rbp),%eax
   2f3ec:	shr    $0x8,%ax
   2f3f0:	and    $0x1,%eax
   2f3f3:	or     %edx,%eax
   2f3f5:	mov    %al,-0x17(%rbp)
   2f3f8:	movzwl -0x24(%rbp),%eax
   2f3fc:	mov    %al,-0x16(%rbp)
   2f3ff:	movzwl -0x2a(%rbp),%eax
   2f403:	shr    $0x8,%ax
   2f407:	mov    %al,-0x15(%rbp)
   2f40a:	movzwl -0x2a(%rbp),%eax
   2f40e:	mov    %al,-0x14(%rbp)
   2f411:	movzwl -0x28(%rbp),%eax
   2f415:	shr    $0x4,%ax
   2f419:	mov    %al,-0x13(%rbp)
   2f41c:	movzwl -0x28(%rbp),%eax
   2f420:	shl    $0x4,%eax
   2f423:	mov    %eax,%edx
   2f425:	movzwl -0x22(%rbp),%eax
   2f429:	shr    $0x8,%ax
   2f42d:	or     %edx,%eax
   2f42f:	mov    %al,-0x12(%rbp)
   2f432:	movzwl -0x22(%rbp),%eax
   2f436:	mov    %al,-0x11(%rbp)
   2f439:	mov    -0x20(%rbp),%rax
   2f43d:	mov    -0x18(%rbp),%rdx
   2f441:	mov    -0x8(%rbp),%rcx
   2f445:	sub    %fs:0x28,%rcx
   2f44e:	je     2f455 <arx::hw_interface::MotorType4::packMotorMsg(double, double, double, double, double)+0x2e5>
   2f450:	call   10ec0 <__stack_chk_fail@plt>
   2f455:	leave
   2f456:	ret
   2f457:	nop

000000000002f458 <arx::hw_interface::MotorType4::packEnableMotor()>:
   2f458:	endbr64
   2f45c:	push   %rbp
   2f45d:	mov    %rsp,%rbp
   2f460:	sub    $0x10,%rsp
   2f464:	mov    %rdi,-0x8(%rbp)
   2f468:	mov    -0x8(%rbp),%rax
   2f46c:	mov    (%rax),%rax
   2f46f:	add    $0x18,%rax
   2f473:	mov    (%rax),%rcx
   2f476:	movsd  0x5a8a(%rip),%xmm0        # 34f08 <typeinfo name for arx::hw_interface::MotorType4+0xa8>
   2f47e:	mov    -0x8(%rbp),%rax
   2f482:	pxor   %xmm4,%xmm4
   2f486:	pxor   %xmm3,%xmm3
   2f48a:	pxor   %xmm2,%xmm2
   2f48e:	movapd %xmm0,%xmm1
   2f492:	mov    0x59ef(%rip),%rdx        # 34e88 <typeinfo name for arx::hw_interface::MotorType4+0x28>
   2f499:	movq   %rdx,%xmm0
   2f49e:	mov    %rax,%rdi
   2f4a1:	call   *%rcx
   2f4a3:	leave
   2f4a4:	ret
   2f4a5:	nop

000000000002f4a6 <arx::hw_interface::MotorType4::packSetZero()>:
   2f4a6:	endbr64
   2f4aa:	push   %rbp
   2f4ab:	mov    %rsp,%rbp
   2f4ae:	sub    $0x30,%rsp
   2f4b2:	mov    %rdi,-0x28(%rbp)
   2f4b6:	mov    %fs:0x28,%rax
   2f4bf:	mov    %rax,-0x8(%rbp)
   2f4c3:	xor    %eax,%eax
   2f4c5:	movb   $0x4,-0x1c(%rbp)
   2f4c9:	movl   $0x7ff,-0x20(%rbp)
   2f4d0:	movb   $0x0,-0x18(%rbp)
   2f4d4:	mov    -0x28(%rbp),%rax
   2f4d8:	mov    0xa0(%rax),%eax
   2f4de:	mov    %al,-0x17(%rbp)
   2f4e1:	movb   $0x0,-0x16(%rbp)
   2f4e5:	movb   $0x3,-0x15(%rbp)
   2f4e9:	mov    -0x20(%rbp),%rax
   2f4ed:	mov    -0x18(%rbp),%rdx
   2f4f1:	mov    -0x8(%rbp),%rcx
   2f4f5:	sub    %fs:0x28,%rcx
   2f4fe:	je     2f505 <arx::hw_interface::MotorType4::packSetZero()+0x5f>
   2f500:	call   10ec0 <__stack_chk_fail@plt>
   2f505:	leave
   2f506:	ret
   2f507:	nop

000000000002f508 <arx::hw_interface::MotorType4::packDisableMotor()>:
   2f508:	endbr64
   2f50c:	push   %rbp
   2f50d:	mov    %rsp,%rbp
   2f510:	sub    $0x10,%rsp
   2f514:	mov    %rdi,-0x8(%rbp)
   2f518:	mov    -0x8(%rbp),%rax
   2f51c:	mov    (%rax),%rax
   2f51f:	add    $0x18,%rax
   2f523:	mov    (%rax),%rcx
   2f526:	movsd  0x59e2(%rip),%xmm0        # 34f10 <typeinfo name for arx::hw_interface::MotorType4+0xb0>
   2f52e:	mov    -0x8(%rbp),%rax
   2f532:	pxor   %xmm4,%xmm4
   2f536:	pxor   %xmm3,%xmm3
   2f53a:	pxor   %xmm2,%xmm2
   2f53e:	movapd %xmm0,%xmm1
   2f542:	mov    0x593f(%rip),%rdx        # 34e88 <typeinfo name for arx::hw_interface::MotorType4+0x28>
   2f549:	movq   %rdx,%xmm0
   2f54e:	mov    %rax,%rdi
   2f551:	call   *%rcx
   2f553:	leave
   2f554:	ret
   2f555:	nop

000000000002f556 <arx::hw_interface::MotorType4::resetCircle()>:
   2f556:	endbr64
   2f55a:	push   %rbp
   2f55b:	mov    %rsp,%rbp
   2f55e:	mov    %rdi,-0x8(%rbp)
   2f562:	mov    -0x8(%rbp),%rax
   2f566:	movl   $0x0,0x48(%rax)
   2f56d:	nop
   2f56e:	pop    %rbp
   2f56f:	ret

000000000002f570 <arx::hw_interface::MotorType4::getMotorId() const>:
   2f570:	endbr64
   2f574:	push   %rbp
   2f575:	mov    %rsp,%rbp
   2f578:	mov    %rdi,-0x8(%rbp)
   2f57c:	mov    -0x8(%rbp),%rax
   2f580:	mov    0xa0(%rax),%eax
   2f586:	pop    %rbp
   2f587:	ret

000000000002f588 <arx::hw_interface::MotorType4::online()>:
   2f588:	endbr64
   2f58c:	push   %rbp
   2f58d:	mov    %rsp,%rbp
   2f590:	sub    $0x30,%rsp
   2f594:	mov    %rdi,-0x28(%rbp)
   2f598:	mov    %fs:0x28,%rax
   2f5a1:	mov    %rax,-0x8(%rbp)
   2f5a5:	xor    %eax,%eax
   2f5a7:	call   10450 <std::chrono::_V2::system_clock::now()@plt>
   2f5ac:	mov    %rax,-0x20(%rbp)
   2f5b0:	mov    -0x28(%rbp),%rax
   2f5b4:	lea    0x30(%rax),%rdx
   2f5b8:	lea    -0x20(%rbp),%rax
   2f5bc:	mov    %rdx,%rsi
   2f5bf:	mov    %rax,%rdi
   2f5c2:	call   10a40 <std::common_type<std::chrono::duration<long, std::ratio<1l, 1000000000l> >, std::chrono::duration<long, std::ratio<1l, 1000000000l> > >::type std::chrono::operator-<std::chrono::_V2::system_clock, std::chrono::duration<long, std::ratio<1l, 1000000000l> >, std::chrono::duration<long, std::ratio<1l, 1000000000l> > >(std::chrono::time_point<std::chrono::_V2::system_clock, std::chrono::duration<long, std::ratio<1l, 1000000000l> > > const&, std::chrono::time_point<std::chrono::_V2::system_clock, std::chrono::duration<long, std::ratio<1l, 1000000000l> > > const&)@plt>
   2f5c7:	mov    %rax,-0x10(%rbp)
   2f5cb:	lea    -0x10(%rbp),%rax
   2f5cf:	mov    %rax,%rdi
   2f5d2:	call   10600 <std::enable_if<std::chrono::__is_duration<std::chrono::duration<long, std::ratio<1l, 1000000l> > >::value, std::chrono::duration<long, std::ratio<1l, 1000000l> > >::type std::chrono::duration_cast<std::chrono::duration<long, std::ratio<1l, 1000000l> >, long, std::ratio<1l, 1000000000l> >(std::chrono::duration<long, std::ratio<1l, 1000000000l> > const&)@plt>
   2f5d7:	mov    %rax,-0x18(%rbp)
   2f5db:	lea    -0x18(%rbp),%rax
   2f5df:	mov    %rax,%rdi
   2f5e2:	call   10bc0 <std::chrono::duration<long, std::ratio<1l, 1000000l> >::count() const@plt>
   2f5e7:	cmp    $0x186a0,%rax
   2f5ed:	setg   %al
   2f5f0:	test   %al,%al
   2f5f2:	je     2f5fe <arx::hw_interface::MotorType4::online()+0x76>
   2f5f4:	mov    -0x28(%rbp),%rax
   2f5f8:	movb   $0x0,0x28(%rax)
   2f5fc:	jmp    2f606 <arx::hw_interface::MotorType4::online()+0x7e>
   2f5fe:	mov    -0x28(%rbp),%rax
   2f602:	movb   $0x1,0x28(%rax)
   2f606:	mov    -0x28(%rbp),%rax
   2f60a:	movzbl 0x28(%rax),%eax
   2f60e:	mov    -0x8(%rbp),%rdx
   2f612:	sub    %fs:0x28,%rdx
   2f61b:	je     2f622 <arx::hw_interface::MotorType4::online()+0x9a>
   2f61d:	call   10ec0 <__stack_chk_fail@plt>
   2f622:	leave
   2f623:	ret

000000000002f624 <arx::hw_interface::MotorType4::~MotorType4()>:
   2f624:	endbr64
   2f628:	push   %rbp
   2f629:	mov    %rsp,%rbp
