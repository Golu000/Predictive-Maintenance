import React, { useState, useEffect, useMemo } from 'react'; // Added useMemo
import { Container, Row, Col, Card, Spinner, Pagination, Form } from 'react-bootstrap'; // Added Form
import { GrHostMaintenance } from "react-icons/gr";
import { SiFsecure } from "react-icons/si";

function Upcoming() {
  const [upcomingDevices, setUpcomingDevices] = useState([]); // To store the fetched device data
  const [loading, setLoading] = useState(true); // To manage loading state
  const [error, setError] = useState(null);     // To manage error state

  // State for filter (for Upcoming Maintenance)
  const [filterDeviceName, setFilterDeviceName] = useState(''); // New state for device name filter

  // States for pagination
  const [currentPage, setCurrentPage] = useState(1);
  const cardsPerPage = 8; // Display 8 cards per page
  const maxPageButtons = 10; //Display Max Page Buttons

  useEffect(() => {
    const fetchUpcomingMaintenance = async () => {
      try {
        // Check sessionStorage first
        const cachedData = sessionStorage.getItem('upcomingMaintenanceData');
        if (cachedData) {
          setUpcomingDevices(JSON.parse(cachedData));
          setLoading(false);
          return; // Use cached data, no API call needed
        }

        // If not in cache, fetch from API
        const response = await fetch('http://localhost:8085/maintenance/upcoming-maintenance');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.success && data.upcoming_maintenance_devices) {
          setUpcomingDevices(data.upcoming_maintenance_devices);
          // Store data in sessionStorage for future navigations within the session
          sessionStorage.setItem('upcomingMaintenanceData', JSON.stringify(data.upcoming_maintenance_devices));
        } else {
          setUpcomingDevices([]); // Set to empty array if no devices or success is false
        }
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchUpcomingMaintenance();
  }, []);

  // Generate unique device names for the dropdown
  const uniqueDeviceNames = useMemo(() => {
    const names = new Set();
    if (upcomingDevices) {
      upcomingDevices.forEach(item => {
        if (item.device_name) { // Assuming 'device_name' is the field for device names
          names.add(item.device_name);
        }
      });
    }
    const sortedNames = Array.from(names).sort((a, b) => a.localeCompare(b));
    return sortedNames;
  }, [upcomingDevices]);

  // Filtering logic for upcoming maintenance cards
  const filteredUpcomingDevices = upcomingDevices
    ? upcomingDevices.filter(item =>
      item.device_name.toLowerCase().includes(filterDeviceName.toLowerCase())
    )
    : [];

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

  // Pagination calculations - now based on filteredUpcomingDevices
  const indexOfLastCard = currentPage * cardsPerPage;
  const indexOfFirstCard = indexOfLastCard - cardsPerPage;
  const currentCards = filteredUpcomingDevices.slice(indexOfFirstCard, indexOfLastCard); // Use filtered data

  const totalPages = Math.ceil(filteredUpcomingDevices.length / cardsPerPage); // Use filtered data

  // Logic to determine which page numbers to display in the pagination controls
  const getVisiblePageNumbers = () => {
    let pages = [];
    if (totalPages <= maxPageButtons) {
      // If total pages are less than or equal to max, show all pages
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      // Calculate start and end pages for the sliding window
      let startPage = Math.max(1, currentPage - Math.floor(maxPageButtons / 2));
      let endPage = startPage + maxPageButtons - 1;

      // Adjust if endPage goes beyond totalPages
      if (endPage > totalPages) {
        endPage = totalPages;
        startPage = Math.max(1, endPage - maxPageButtons + 1); // Re-adjust startPage
      }

      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
    }
    return pages;
  };

  const visiblePageNumbers = getVisiblePageNumbers();

  // Function to change page
  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Handler for filter change, resets page to 1
  const handleFilterChange = (e) => {
    setFilterDeviceName(e.target.value);
    setCurrentPage(1); // Reset to first page when filter changes
  };

  return (
    <Container fluid className="py-4 dashboard-container">
      <h3 className="text-center mb-4 text-light">Upcoming Maintenance Within Next Six Months</h3>

      {/* Dropdown Filter for Device Names */}
      <Row className="justify-content-center mb-4">
        <Col xs={12} md={6} lg={4}>
          <Form.Select
            aria-label="Filter by device name"
            value={filterDeviceName}
            onChange={handleFilterChange}
            className="bg-light text-dark border-secondary"
          >
            <option value="">All Devices</option>
            {uniqueDeviceNames.map((name, index) => (
              <option key={index} value={name}>{name}</option>
            ))}
          </Form.Select>
        </Col>
      </Row>

      <Row className="justify-content-center g-4"> {/* Using g-4 for consistent gutter */}
        {currentCards.length > 0 ? (
          currentCards.map((device, index) => (
            <Col key={index} xs={12} sm={6} md={4} lg={3}>
              {/* <Card bg="primary" text="white" className="shadow-lg h-100 rounded">  */}
              <Card style={{ backgroundColor: 'rgba(255, 255, 255, 0.7)', borderColor: 'rgba(255, 255, 255, 0.7)' }} className="text-black shadow-lg h-100 rounded">
                <Card.Body className="d-flex flex-column justify-content-between">
                  <div className="d-flex align-items-center mb-3">
                    <div className="me-3 fs-2"><GrHostMaintenance /></div>
                    <Card.Title className="mb-0 fs-5">Device: {device.device_name}</Card.Title>
                  </div>
                  <Card.Text className="fs-6">
                    {/* <strong>Device ID:</strong> {device.device_id}<br /> */}
                    <strong>Room No:</strong> {device.room_no}<br />
                    <strong>Device Year:</strong> {device.device_year}<br />
                    <strong>Previous Issue Reported:</strong> {device.issue_reported || 'N/A'}<br />
                    <strong>Next Maintenance Date:</strong><span className="fw-bold text-primary"> {device.next_maintenance_date}<br /></span>
                    <strong>Previous Maintenance Date:</strong> {device.previous_maintenance_date || 'N/A'}<br />
                    <strong>Predicted Days Since Maintenance:</strong> {device.predictedDaysSinceMaintenance ? device.predictedDaysSinceMaintenance.toFixed(2) : 'N/A'}<br />
                    <strong>Under Warranty:</strong> <SiFsecure /> {device.under_warranty ? device.under_warranty.toUpperCase() : 'N/A'}<br />
                    <strong>Warranty Year Till:</strong> {device.warranty_year_till || 'N/A'}
                  </Card.Text>
                    <div className="text-end mt-2">
                      <span className="badge bg-primary text-white ai-badge">AI-Powered Prediction</span>
                    </div>
                </Card.Body>
              </Card>
            </Col>
          ))
        ) : (
          <Col xs={12}>
            <p className="text-center text-secondary fs-5">
              {filterDeviceName ? `No upcoming maintenance found for "${filterDeviceName}" devices.` : 'No upcoming maintenance devices found.'}
            </p>
          </Col>
        )}
      </Row>
      {/* Pagination Controls */}
      {totalPages > 1 && ( // Only show pagination if there's more than 1 page
        <Row className="justify-content-center mt-4">
          <Col xs="auto">
            <Pagination className="custom-pagination"> {/* Add a class for potential custom styling */}
              {/* Go to First Page Button */}
              <Pagination.First onClick={() => paginate(1)} disabled={currentPage === 1} />

              {/* Previous Page Button */}
              <Pagination.Prev onClick={() => paginate(currentPage - 1)} disabled={currentPage === 1} />

              {/* Ellipsis before page numbers if necessary */}
              {visiblePageNumbers[0] > 1 && <Pagination.Ellipsis />}

              {/* Visible Page Number Buttons */}
              {visiblePageNumbers.map((pageNumber) => (
                <Pagination.Item
                  key={pageNumber}
                  active={pageNumber === currentPage}
                  onClick={() => paginate(pageNumber)}
                >
                  {pageNumber}
                </Pagination.Item>
              ))}

              {/* Ellipsis after page numbers if necessary */}
              {visiblePageNumbers[visiblePageNumbers.length - 1] < totalPages && <Pagination.Ellipsis />}

              {/* Next Page Button */}
              <Pagination.Next onClick={() => paginate(currentPage + 1)} disabled={currentPage === totalPages} />

              {/* Go to Last Page Button */}
              <Pagination.Last onClick={() => paginate(totalPages)} disabled={currentPage === totalPages} />
            </Pagination>
          </Col>
        </Row>
      )}
    </Container>
  );
}

export default Upcoming;
