import React, { useState } from 'react';
import star from './star1.svg';
import './App.css';

function LoginForm({ userData, setUserData }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleSubmit = async (event) => {
    event.preventDefault(); // Prevent default form submission behavior
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
      <button type="submit" value="Login Or Register">Submit</button>
    </form>
  );
}

function App() {
  // const [message, setMessage] = useState("Something");
  const [userData, setUserData] = useState(null);

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
            <p>Logged in User ID: {userData.id}</p>
            <p>User data: { userData.edges }</p>
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
        {userData && userData.success === "no" && <p>Failed to login</p>}
      </header>
    </div>
  );
}

export default App;
