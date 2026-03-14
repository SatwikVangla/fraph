import Hero from "./components/Hero";
import DatasetUpload from "./components/DatasetUpload";
import FraudGraph from "./components/FraudGraph";

export default function App() {
return ( <div className="bg-black text-white min-h-screen">


  {/* HERO SECTION */}
  <Hero />

  {/* GRAPH LAB SECTION */}
  <section className="px-10 py-20">

    <h2 className="text-4xl font-bold text-center mb-12">
      FRAPH Graph Lab
    </h2>

    {/* DATASET UPLOAD */}
    <DatasetUpload />

    {/* FRAUD GRAPH */}
    <div className="mt-16">
      <FraudGraph />
    </div>

  </section>

</div>


);
}

