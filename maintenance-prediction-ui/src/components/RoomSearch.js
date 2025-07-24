import React, { useState, useEffect } from 'react';
import { Container, Row, Col, Card, Spinner } from 'react-bootstrap';
import { MdOutlineDevicesOther } from "react-icons/md";
import { FaCalendarDay } from "react-icons/fa6";
import { FaCalendarCheck } from "react-icons/fa";
import { SiFsecure } from "react-icons/si";

function RoomSearch() {
    const [roomNumber, setRoomNumber] = useState(null);
    const [deviceDetails, setDeviceDetails] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
  
    useEffect(() => {
      // Parse the room number from the URL query parameters
      const queryParams = new URLSearchParams(window.location.search);
      const room = queryParams.get('roomNumber');
  
      if (room) {
        setRoomNumber(room);
        const fetchRoomDevices = async () => {
          try {
            setLoading(true);
            setError(null);
            setDeviceDetails([]); // Clear previous results
  
            const response = await fetch('http://localhost:8085/maintenance/search', {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              body: JSON.stringify({ "Room Number": parseInt(room) }),
            });
  
            if (!response.ok) {
              throw new Error(`HTTP error! status: ${response.status}, Please enter a valid Room Number`);
            }
  
            const data = await response.json();
            if (data.success && data.predictions) {
              setDeviceDetails(data.predictions);
            } else {
              setDeviceDetails([]); // No predictions or success false
            }
          } catch (e) {
            setError(e.message);
            setDeviceDetails([]);
          } finally {
            setLoading(false);
          }
        };
  
        fetchRoomDevices();
      } else {
        setLoading(false);
        setError("No room number provided in the URL.");
      }
    }, [roomNumber]); // Re-run effect if roomNumber changes (e.g., if navigated to a different room via URL)
  
    if (loading) {
      return (
        <Container fluid className="py-4 dashboard-container d-flex justify-content-center align-items-center" style={{ minHeight: 'calc(100vh - 56px)' }}>
        <Spinner animation="border" role="status" className="text-light" style={{ width: '4rem', height: '4rem' }}>
          <span className="visually-hidden">Loading...</span>
        </Spinner>
        <p className='text-light'> Loading...</p>
        </Container>
      );
    }
  
    if (error) {
      return (
        <Container fluid className="py-4 dashboard-container">
          <p className="fs-4">Error: {error}</p>
        </Container>
      );
    }
  
    return (
      <Container fluid className="py-4 dashboard-container">
        <h3 className="text-center mb-4 text-light">Device Details For Room Number: {roomNumber}</h3>
        {deviceDetails.length > 0 ? (
          <Row className="justify-content-center g-4">
            {deviceDetails.map((device, index) => (
              <Col key={index} xs={12} sm={6} md={4} lg={3}>
                {/* <Card bg="info" text="white" className="shadow-lg h-100 rounded"> */}
                <Card border="dark" style={{ backgroundColor: 'rgba(255, 255, 255, 0.7)'}}>
                  <Card.Body className="d-flex flex-column justify-content-between">
                    <div className="d-flex align-items-center mb-3">
                      <div className="me-3 fs-2"><MdOutlineDevicesOther /></div>
                      <Card.Title className="mb-0 fs-5">{device.deviceName}</Card.Title>
                    </div>
                    <Card.Text className="fs-6">
                      {/* <strong>Device ID:</strong> {device.device_id}<br /> */}
                      <strong>Device Year:</strong> {device.deviceYear}<br />
                      <strong>Previous Issue Reported:</strong> {device.issueReported || 'N/A'}<br />
                      <strong>Next Maintenance:</strong> <FaCalendarDay /> {device.nextMaintenanceDate}<br />
                      <strong>Previous Maintenance:</strong> <FaCalendarCheck /> {device.previous_maintenance_date || 'N/A'}<br />
                      <strong>Days Since Last Maintenance:</strong> {device.predictedDaysSinceMaintenance ? device.predictedDaysSinceMaintenance.toFixed(2) : 'N/A'}<br />
                      <strong>Under Warranty:</strong> <SiFsecure /> {device.under_warranty ? device.under_warranty.toUpperCase() : 'N/A'}<br />
                      <strong>Warranty Till:</strong> {device.warranty_year_till || 'N/A'}
                    </Card.Text>
                      <div className="text-end mt-2">
                        <span className="badge bg-primary text-white ai-badge">AI-Powered Prediction</span>
                      </div>
                  </Card.Body>
                </Card>
              </Col>
            ))}
          </Row>
        ) : (
          <p className="text-center text-secondary fs-5">No devices found for Room {roomNumber}.</p>
        )}
      </Container>
    );
  }
  
  export default RoomSearch;