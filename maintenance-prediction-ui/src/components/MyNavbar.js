import React, { useState } from 'react';
import Button from 'react-bootstrap/Button';
import Container from 'react-bootstrap/Container';
import Form from 'react-bootstrap/Form';
import Nav from 'react-bootstrap/Nav';
import Navbar from 'react-bootstrap/Navbar';
import { FaSearch, FaTools } from 'react-icons/fa';
import { TbLayoutDashboardFilled } from 'react-icons/tb';
import { AiFillSchedule } from "react-icons/ai";
import '../styles/styles.css';
import logo from '../assets/marriott.png';

function MyNavbar() {
  const [roomNumberInput, setRoomNumberInput] = useState('');

  const handleInputChange = (e) => {
    setRoomNumberInput(e.target.value);
  };

  const handleSearch = (e) => {
    e.preventDefault(); // Prevent default form submission
    if (roomNumberInput) {
      window.location.href = `/room-search-results?roomNumber=${roomNumberInput}`;
    } else {
      // Optional: Add some user feedback if the input is empty
      console.log("Please enter a room number to search.");
    }
  };

  return (
    <Navbar expand="lg" className="main-nav">
      <Container fluid>
        <Navbar.Toggle aria-controls="navbarScroll" className="custom-toggler" />
        <Navbar.Brand href="/dashboard"><img src={logo} alt="Marriott Bonvoy Logo" className="navbar-logo" /> Smart Operations</Navbar.Brand>
        <Navbar.Collapse id="navbarScroll">
          <Nav className="ms-auto my-2 my-lg-0" navbarScroll>
            <Nav.Link href="/dashboard"><TbLayoutDashboardFilled className="me-1" /> Maintenance Dashboard</Nav.Link>
            <Nav.Link href='/scheduled-maintenance'><AiFillSchedule className='me-1 '/>Scheduled Maintenance</Nav.Link>
            <Nav.Link href="/upcoming-maintenance"><FaTools className="me-1" /> Upcoming Maintenance</Nav.Link>
          </Nav>
          <Form className="d-flex" onSubmit={handleSearch}>
            <Form.Control 
              type="search" 
              placeholder="Room Number" 
              className="me-2" 
              aria-label="Search" 
              value={roomNumberInput}
              onChange={handleInputChange}/>
            <Button type="submit" variant="outline-success"><FaSearch /></Button>
          </Form>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default MyNavbar;