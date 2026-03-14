import PlaceholderGraph from "../components/PlaceholderGraph";

export default function DashboardPage() {

return (


<div className="min-h-screen bg-black text-white p-12">

  {/* PAGE TITLE */}

  <h1 className="text-5xl font-black mb-16 tracking-wide">
    FRAUD INTELLIGENCE DASHBOARD
  </h1>


  {/* METRIC CARDS */}

  <div className="grid grid-cols-3 gap-10 mb-16">

    <div className="bg-neutral-900 p-8 rounded-xl border border-neutral-800">
      <h2 className="text-xl mb-4 text-neutral-400">
        Transactions Analyzed
      </h2>
      <p className="text-4xl font-bold">--</p>
    </div>

    <div className="bg-neutral-900 p-8 rounded-xl border border-neutral-800">
      <h2 className="text-xl mb-4 text-neutral-400">
        Fraudulent Accounts
      </h2>
      <p className="text-4xl font-bold text-red-500">--</p>
    </div>

    <div className="bg-neutral-900 p-8 rounded-xl border border-neutral-800">
      <h2 className="text-xl mb-4 text-neutral-400">
        Network Risk Score
      </h2>
      <p className="text-4xl font-bold">--</p>
    </div>

  </div>


  {/* GRAPH SECTION */}

  <div className="bg-neutral-900 h-[500px] rounded-xl border border-neutral-800 flex items-center justify-center mb-16">

    <PlaceholderGraph />

  </div>


  {/* SUSPICIOUS TRANSACTIONS TABLE */}

  <div className="bg-neutral-900 rounded-xl border border-neutral-800 p-10">

    <h2 className="text-2xl mb-8">
      Suspicious Transactions
    </h2>

    <table className="w-full text-left">

      <thead className="text-neutral-400 border-b border-neutral-700">
        <tr>
          <th className="pb-4">Account</th>
          <th className="pb-4">Transaction</th>
          <th className="pb-4">Amount</th>
          <th className="pb-4">Risk Level</th>
        </tr>
      </thead>

      <tbody className="text-neutral-300">

        <tr className="border-b border-neutral-800">
          <td className="py-4">---</td>
          <td>---</td>
          <td>---</td>
          <td className="text-red-500">---</td>
        </tr>

        <tr className="border-b border-neutral-800">
          <td className="py-4">---</td>
          <td>---</td>
          <td>---</td>
          <td className="text-red-500">---</td>
        </tr>

      </tbody>

    </table>

  </div>


</div>


);
}

