import React, { useState } from 'react';
import star from './star1.svg';
import './App.css';
import axios from 'axios';

import { ReactFlow, Background } from "@xyflow/react";

import '@xyflow/react/dist/style.css';

const verticalHeightQuantum = 200;
const horizontalWidthQuantum = 200;


function AssetTree({ userData }) {
  const [nodes, setNodes] = useState([]);
  const [edges, setEdges] = useState([]);

  const handleSubmit = async (event) => {
    event.preventDefault(); // Prevent default form submission behavior
    const response = await fetch('/get_asset_tree', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({ userid: userData.id }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || 'Failed to get asset tree')
    }
    const data = await response.json();
    const cur_nodes = [];
    const cur_edges = [];
    for (let i = 0; i < data.nodes_info.length; i++) {
      const node_info = data.nodes_info[i];
      cur_nodes.push({
        id: node_info.id,
        position: { x: node_info.horizontal_level * horizontalWidthQuantum, y: node_info.vertical_level * verticalHeightQuantum },
        data: { label: node_info.label },
        style: {
          background: node_info.type === 'Descriptor' ? '#ccffcc' :
            node_info.type === 'Asset' ? '#ffcccc' :
              node_info.type === 'User' ? '#cce6ff' : '#ffffff',
          color: node_info.type === 'Descriptor' ? '#006600' :
            node_info.type === 'Asset' ? '#660000' :
              node_info.type === 'User' ? '#003366' : '#000000',
          border: node_info.type === 'Descriptor' ? '1px solid #006600' :
            node_info.type === 'Asset' ? '1px solid #660000' :
              node_info.type === 'User' ? '1px solid #003366' : '1px solid #000000',
          // bold text
          fontWeight: 'bold',
        },
      });
      if (node_info.parent) {
        cur_edges.push({
          id: `e${node_info.parent}-${node_info.id}`,
          source: node_info.parent,
          target: node_info.id,
        });
      }
    }
    setNodes(cur_nodes);
    setEdges(cur_edges);
    console.log(cur_nodes);
  }

  return (
    <div style={{ marginTop: '20px' }} className='App-body'>
      <form onSubmit={handleSubmit}>
        <button type="submit" value="Get Asset Tree">Get Asset Tree</button>
        <p></p>
        {nodes.length > 0 && edges.length > 0 &&
          <div style={{
            width: '90vw',
            height: '90vh',
            margin: '0 auto',  // Centers horizontally
            display: 'flex',   // Enables flexbox
            justifyContent: 'center', // Centers horizontally in flex container
            alignItems: 'center'      // Centers vertically in flex container
          }} className='App-graph'>
            <ReactFlow nodes={nodes} edges={edges} >
            </ReactFlow>
          </div>
        }
      </form>
    </div>
  );
}

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
    <form onSubmit={handleSubmit}>
      <label>
        Username:
        <input type="text" name="username" onChange={(e) => setUsername(e.target.value)} />
      </label>
      <br />
      <label>
        Password:
        <input type="password" name="password" onChange={(e) => setPassword(e.target.value)} />
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
            Welcome to Pollux
            <p className='App-header-small-text'>User: {userData.name} (ID:{userData.id.split(":")[1]})</p>
          </header>
          <div className='App-body'>
            <h4>What Should We Do?</h4>
            <div>
              <FileUploader userData={userData} setImageData={setImageData} />
              {imageData && imageData.success === "yes" && <p>{imageData.id} Uploaded</p>}
              {imageData && imageData.success === "no" && <p>Upload Failed!</p>}
              <br />
              <DescriptorUploader userData={userData} setDescriptorData={setDescriptorData} />
              {descriptorData && descriptorData.success === "yes" && <p>Descriptor Added: {descriptorData.descriptorid.split(":")[1]}</p>}
              {descriptorData && descriptorData.success === "no" && <p>Failed to add Descriptor!</p>}
              <br />
              <button onClick={() => setUserData(null)}>Logout</button>
              <AssetTree userData={userData} />
            </div>
          </div>
        </div >
      );
    }
  }

  return (
    <div className="App">
      <header className="App-header" style={{ height: '100vh' }}>
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
