
import ParticleBackground from "./ParticleBackground";

export default function Hero() {
  return (
    <section className="relative h-screen bg-black text-white flex items-center justify-center">

      <ParticleBackground />

      <div className="relative z-10 text-center space-y-6">

        <h1 className="text-7xl font-bold tracking-widest">
          FRAPH
        </h1>

        <p className="text-xl text-gray-300">
          Fraud Recognition using Advanced Graph Processing
        </p>

        <p className="text-gray-400 max-w-xl mx-auto">
          Detect financial fraud using Graph Neural Networks
          by analyzing complex transaction networks.
        </p>

        <button className="border border-white px-6 py-3 hover:bg-white hover:text-black transition">
          Upload Dataset
        </button>

      </div>

    </section>
  );
}
