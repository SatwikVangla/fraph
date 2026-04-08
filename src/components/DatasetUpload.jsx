import { useState } from "react";

import { API_BASE_URL } from "../utils/api";

export default function DatasetUpload() {
const [file, setFile] = useState(null);

const uploadFile = async () => {
const formData = new FormData();
formData.append("file", file);


await fetch(`${API_BASE_URL}/upload`, {
  method: "POST",
  body: formData
});

alert("Dataset uploaded successfully");
};

return ( <div className="text-center">
  <input
    type="file"
    onChange={(e) => setFile(e.target.files[0])}
    className="text-white"
  />

  <button
    onClick={uploadFile}
    className="ml-4 px-6 py-2 border border-red-600 hover:bg-red-600 transition"
  >
    Upload Dataset
  </button>

</div>
);
}
