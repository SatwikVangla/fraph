import Spline from "@splinetool/react-spline";
import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import ParticleBackground from "./ParticleBackground";

export default function Hero() {
	const navigate = useNavigate();
	const [showSpline, setShowSpline] = useState(false);
	const titleRef = useRef(null);

	useEffect(() => {
		const frameId = window.requestAnimationFrame(() => {
			setShowSpline(true);
		});
		return () => {
			window.cancelAnimationFrame(frameId);
		};
	}, []);

	const handleMouseMove = (e) => {

		const x = (e.clientX / window.innerWidth - 0.5) * 15;
		const y = (e.clientY / window.innerHeight - 0.5) * 15;

		if (titleRef.current) {

			titleRef.current.style.transform =
				`translate3d(${x}px, ${y}px, 0)`;

			titleRef.current.style.textShadow =
				`${-x}px ${-y}px 0 rgba(255,0,0,0.6)`;
		}
	};

	return (
		<section
		onMouseMove={handleMouseMove}
		className="relative isolate flex h-screen w-full items-center justify-center overflow-hidden bg-black text-white"
		>

		{/* SPLINE BACKGROUND */}
		<div className="absolute inset-0 z-0 pointer-events-none">
		{showSpline ? (
			<Spline
			scene="https://prod.spline.design/2cc82344-8f3c-4702-92a0-e9276e998ae9/scene.splinecode"
			style={{
				width: "100%",
					height: "100%",
					pointerEvents: "none"
			}}
			/>
		) : null}
		</div>

		{/* PARTICLE NETWORK */}
		<div className="absolute inset-0 z-10 pointer-events-none opacity-40">
		<ParticleBackground />
		</div>

		{/* WAVY OVERLAY */}
		<div className="wavy-texture absolute inset-0 z-20 pointer-events-none" />

		{/* RADIAL DARKENING */}
		<div
		className="absolute inset-0 pointer-events-none"
		style={{
			background:
			"radial-gradient(circle at center, transparent 0%, black 90%)",
				zIndex: 25
		}}
		/>

		{/* CONTENT */}
		<div className="relative z-[100] text-center space-y-8 select-none">

		<h1
		ref={titleRef}
		className="glitch-text text-8xl md:text-[10rem] font-black tracking-tighter transition-transform duration-75"
		>
		FRAPH
		</h1>

		<div className="space-y-4 pointer-events-auto">

		<p className="text-lg md:text-xl font-bold tracking-[0.4em] text-red-600 uppercase">
		Fraud Recognition <span className="text-white">/</span> Graph Intelligence
		</p>

		<button
		onClick={() => navigate("/upload")}
		className="btn-glow mt-8 px-12 py-4 bg-transparent border-2 border-red-600 text-white font-black uppercase tracking-widest hover:bg-red-600 transition-all duration-300"
		>
		Analyze Network
		</button>
		</div>

		</div>

		</section>
	);
}
