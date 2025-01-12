import React, { useState } from 'react';
import star from './star1.svg';
import './App.css';
import axios from 'axios';

function LoginForm({ userData, setUserData }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault(); // Prevent default form submission behavior
    if (event.nativeEvent.submitter.value === "login") {
      const response = await fetch('/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to sign in')
      }
      const data = await response.json();
      setUserData(data);
    } else if (event.nativeEvent.submitter.value === "register") {
      const response = await fetch('/register', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to register')
      }
      const data = await response.json();
      setUserData(data);
    }
  };
  return (
    <form onSubmit={handleSubmit }>
      <label>
        Username:
        <input type="text" name="username" onChange={(e) => setUsername(e.target.value)}/>
      </label>
      <br />
      <label>
        Password:
        <input type="password" name="password" onChange={(e) => setPassword(e.target.value)}/>
      </label>
      <br />
      <button type="submit" value="login">Login</button>
      <button type="submit" value="register">Register</button>
    </form>
  );
}

function FileUploader({ userData, setImageData }) {

  const handleSubmit = async (event) => {
    event.preventDefault(); // Prevent default form submission behavior
    const formData = new FormData();
    formData.append('file', event.target.file.files[0]);
    formData.append('userid', userData.id);
    const response = await axios.post(
      '/upload',
      formData,
      {
        headers: {
        'Content-Type': 'multipart/form-data',
        },
      });

    const data = response.data;
    console.log(data);
    setImageData(data);
  }
  return (
    <form onSubmit={handleSubmit}>
      <input type="file" name="file" />
      <button type="submit" value="Upload">Upload</button>
    </form>
  );
}

function DescriptorUploader({ userData, setDescriptorData }) {
  const handleSubmit = async (event) => {
    event.preventDefault(); // Prevent default form submission behavior
    const formData = new FormData();
    formData.append('userid', userData.id);
    formData.append('descriptor_name', event.target.descriptor.value);
    const response = await axios.post(
      '/add_descriptor',
      formData,
      {
        headers: {
        'Content-Type': 'multipart/form-data',
        },
      });

    const data = response.data;
    console.log(data);
    setDescriptorData(data);
  }
  return (
    <form onSubmit={handleSubmit}>
      <input type="text" name="descriptor" />
      <button type="submit" value="Upload">Add Asset Category</button>
    </form>
  );
}


function App() {
  // const [message, setMessage] = useState("Something");
  const [userData, setUserData] = useState(null);
  const [imageData, setImageData] = useState(null);
  const [descriptorData, setDescriptorData] = useState(null);

  // useEffect(() => { 
  //   fetch('/message')
  //     .then((res) => res.json())
  //     .then((data) => setMessage(data.message));
  // }, [])

  if (userData) {
    if (userData.success === "yes") {
      return (
        <div className="App">
          <header className="App-header">
            <img src={star} className="App-logo" alt="logo" />
            <p>
              Welcome to Pollux
            </p>
            <p>Logged in User: {userData.name} (ID:{userData.id.split(":")[1]})</p>
            <div>
              <h4>What Do We Do</h4>
              <div>
                <FileUploader userData={userData} setImageData={setImageData} />
                {imageData && imageData.success === "yes" && <p>{imageData.id} Uploaded</p>}
                {imageData && imageData.success === "no" && <p>Upload Failed!</p>}
                <br />
                <DescriptorUploader userData={userData} setDescriptorData={setDescriptorData} />
                {descriptorData && descriptorData.success === "yes" && <p>Descriptor Added: { descriptorData.descriptorid.split(":")[1]}</p>}
                {descriptorData && descriptorData.success === "no" && <p>Failed to add Descriptor!</p>}
                <br />
                <button>View Asset Tree</button>
              </div>
            </div>
            <div>
              <button onClick={() => setUserData(null)}>Logout</button>
            </div>
          </header>
        </div>
      );
    }
  }

  return (
    <div className="App">
      <header className="App-header">
        <img src={star} className="App-logo" alt="logo" />
        <p>
          Login or Register to access Pollux
        </p>
        <LoginForm userData={userData} setUserData={setUserData} />
        {userData && userData.success === "no" && <p>Failed to login, you might need to register...</p>}
      </header>
    </div>
  );
}

export default App;
