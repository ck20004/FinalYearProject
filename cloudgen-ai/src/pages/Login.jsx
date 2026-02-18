import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

function Login() {
  const [form, setForm] = useState({ email: "", password: "" });
  const navigate = useNavigate();

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
  e.preventDefault();
  try {
    const res = await axios.post("http://localhost:5000/api/auth/login", form);
    localStorage.setItem("token", res.data.token);
    localStorage.setItem("user", JSON.stringify(res.data.user)); // ✅ Add this line
    navigate("/dashboard");
  } catch (err) {
    alert(err.response?.data?.msg || "Login failed");
  }
};


  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-100">
      <div className="card">
        <h2 className="title-blue">Login to CloudGen.AI</h2>
        <form className="space-y-4" onSubmit={handleSubmit}>
          <input name="email" type="email" placeholder="Email" onChange={handleChange} className="input-blue" required />
          <input name="password" type="password" placeholder="Password" onChange={handleChange} className="input-blue" required />
          <button type="submit" className="btn-blue">Login</button>
        </form>
        <p className="text-center text-sm mt-4">
          Don’t have an account? <Link to="/signup" className="text-blue-600 hover:underline">Sign up</Link>
        </p>
      </div>
    </div>
  );
}

export default Login;
