import React, { useState, useEffect, useMemo } from 'react';
import { Container, Row, Col, Card, Spinner, Pagination, Form } from 'react-bootstrap';
import { MdDevicesOther } from "react-icons/md"; // For device icon
import { FaCheckCircle, FaTimesCircle } from 'react-icons/fa'; // Icons for warranty status

function Scheduled() {
  const [scheduledDevices, setScheduledDevices] = useState([]); // To store the fetched device data
  const [loading, setLoading] = useState(true); // To manage loading state
  const [error, setError] = useState(null);     // To manage error state

  // State for filter (for Scheduled Maintenance)
  const [filterDeviceType, setFilterDeviceType] = useState('');

  // States for pagination
  const [currentPage, setCurrentPage] = useState(1);
  const cardsPerPage = 8; // Display 8 cards per page
  const maxPageButtons = 10; // Display Max Page Buttons

  // Get the current year dynamically
  const currentYear = new Date().getFullYear();

  useEffect(() => {
    const fetchScheduledMaintenance = async () => {
      try {
        // Check sessionStorage first
        const cachedData = sessionStorage.getItem('scheduledMaintenanceData');
        if (cachedData) {
          setScheduledDevices(JSON.parse(cachedData));
          setLoading(false);
          return; // Use cached data, no API call needed
        }

        // If not in cache, fetch from API
        const response = await fetch('http://localhost:8085/maintenance/non-room-data');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        if (data.message && Array.isArray(data.non_room_maintenance)) {
          setScheduledDevices(data.non_room_maintenance);
          // Store data in sessionStorage for future navigations within the session
          sessionStorage.setItem('scheduledMaintenanceData', JSON.stringify(data.non_room_maintenance));
        } else {
          setScheduledDevices([]); // Set to empty array if no devices or message is not as expected
        }
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchScheduledMaintenance();
  }, []); // Empty dependency array ensures this runs once per component mount

  // Generate unique device types for the dropdown
  const uniqueDeviceTypes = useMemo(() => {
    const types = new Set();
    if (scheduledDevices) {
      scheduledDevices.forEach(item => {
        if (item.DeviceType) {
          types.add(item.DeviceType);
        }
      });
    }
    const sortedTypes = Array.from(types).sort((a, b) => a.localeCompare(b));
    return sortedTypes;
  }, [scheduledDevices]);

  // Filtering logic for scheduled maintenance cards
  const filteredScheduledDevices = scheduledDevices
    ? scheduledDevices.filter(item =>
      item.DeviceType.toLowerCase().includes(filterDeviceType.toLowerCase())
    )
    : [];

  // Pagination calculations
  const indexOfLastCard = currentPage * cardsPerPage;
  const indexOfFirstCard = indexOfLastCard - cardsPerPage;
  // Use filteredScheduledDevices as the source for slicing
  const currentCards = filteredScheduledDevices.slice(indexOfFirstCard, indexOfLastCard);

  const totalPages = Math.ceil(filteredScheduledDevices.length / cardsPerPage);

  // Logic to determine which page numbers to display in the pagination controls
  const getVisiblePageNumbers = (total, current, maxVisible) => {
    let pages = [];
    if (total <= maxVisible) {
      for (let i = 1; i <= total; i++) {
        pages.push(i);
      }
    } else {
      let startPage = Math.max(1, current - Math.floor(maxVisible / 2));
      let endPage = startPage + maxVisible - 1;

      if (endPage > total) {
        endPage = total;
        startPage = Math.max(1, endPage - maxVisible + 1);
      }
      for (let i = startPage; i <= endPage; i++) {
        pages.push(i);
      }
    }
    return pages;
  };

  const visiblePageNumbers = getVisiblePageNumbers(totalPages, currentPage, maxPageButtons);

  // Function to change page
  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Handler for filter change, resets page to 1
  const handleFilterChange = (e) => {
    setFilterDeviceType(e.target.value);
    setCurrentPage(1); // Reset to first page when filter changes
  };

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
        <p className="fs-4 text-danger">Error: {error}</p>
      </Container>
    );
  }

  return (
    <Container fluid className="py-4 dashboard-container">
      <h3 className="text-center mb-4 text-light">Scheduled Non-Room Maintenance</h3>

      {/* Dropdown Filter for Device Types */}
      <Row className="justify-content-center mb-4">
        <Col xs={12} md={6} lg={4}>
          <Form.Select
            aria-label="Filter by device type"
            value={filterDeviceType}
            onChange={handleFilterChange}
            className="bg-light text-dark border-secondary"
          >
            <option value="">All Devices</option>
            {uniqueDeviceTypes.map((type, index) => (
              <option key={index} value={type}>{type}</option>
            ))}
          </Form.Select>
        </Col>
      </Row>

      <Row className="justify-content-center g-4"> {/* Using g-4 for consistent gutter */}
        {currentCards.length > 0 ? (
          currentCards.map((device, index) => {
            // Determine warranty status dynamically
            const isUnderWarranty = device.WarrantyYear && parseInt(device.WarrantyYear) >= currentYear;
            const warrantyStatusText = isUnderWarranty ? 'Under Warranty' : 'Out of Warranty';
            const warrantyStatusClass = isUnderWarranty ? 'text-success' : 'text-danger';
            const warrantyStatusIcon = isUnderWarranty ? <FaCheckCircle className="ms-1" /> : <FaTimesCircle className="ms-1" />;

            return (
              <Col key={device.DeviceID || index} xs={12} sm={6} md={4} lg={3}>
                <Card style={{ backgroundColor: 'rgba(255, 255, 255, 0.7)', borderColor: 'rgba(255, 255, 255, 0.7)' }} className="text-black shadow-lg h-100 rounded">
                  <Card.Body className="d-flex flex-column justify-content-between">
                    <div className="d-flex align-items-center mb-3">
                      <div className="me-3 fs-2 "><MdDevicesOther /></div> {/* Icon for device type */}
                      <Card.Title className="mb-0 fs-5">{device.DeviceType}</Card.Title>
                    </div>
                    <Card.Text className="fs-6">
                      <strong>Device ID:</strong> {device.DeviceID}<br />
                      <strong>Location:</strong> {device.Location}<br />
                      <strong>Device Year:</strong> {device.DeviceYear}<br />
                      <strong>Last Maintenance:</strong> {device.LastMaintenanceDate}<br />
                      <strong>Next Scheduled:</strong> <span className="fw-bold text-primary">{device.NextScheduledMaintenanceDates}</span><br />
                      {/* <strong>Total Usage:</strong> {device.TotalUsageHours ? `${device.TotalUsageHours.toFixed(2)} hrs` : 'N/A'}<br /> */}
                      <strong>Warranty Till:</strong> {device.WarrantyYear || 'N/A'}<br />
                      <strong>Status:</strong> {' '}
                      <span className={`fw-bold ${warrantyStatusClass}`}>
                        {warrantyStatusText}
                        {warrantyStatusIcon}
                      </span>
                    </Card.Text>
                    <div className="text-end mt-2">
                      <span className="badge bg-secondary text-white">Scheduled Maintenance</span>
                    </div>
                  </Card.Body>
                </Card>
              </Col>
            );
          })
        ) : (
          <Col xs={12}>
            <p className="text-center text-secondary fs-5">
              {filterDeviceType ? `No scheduled maintenance found for "${filterDeviceType}" devices.` : 'No scheduled maintenance items found.'}
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

export default Scheduled;
