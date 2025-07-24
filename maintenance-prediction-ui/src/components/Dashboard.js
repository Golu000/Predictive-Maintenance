import React, { useState, useEffect, useMemo } from 'react';
import { Container, Row, Col, Card, Modal, Button, Form, Pagination, Spinner } from 'react-bootstrap';
import { FaTools, FaCheckCircle, FaExclamationTriangle } from 'react-icons/fa';
import { MdDevicesOther } from "react-icons/md";
import { RiAiGenerate2 } from "react-icons/ri";
import SystemStatusBanner from './SystemStatusBanner';

function Dashboard() {
  const [dashboardData, setDashboardData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  // States for detailed device info modal
  const [showDetailModal, setShowDetailModal] = useState(false);
  const [selectedDeviceDetails, setSelectedDeviceDetails] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);
  const [detailError, setDetailError] = useState(null);
  // State for filter (for Pending Maintenance)
  const [filterDeviceName, setFilterDeviceName] = useState('');
  // State for AI Weekly Maintenance filter
  const [aiFilterDeviceName, setAiFilterDeviceName] = useState('');
  // States for Pending Maintenance pagination
  const [currentPage, setCurrentPage] = useState(1);
  const cardsPerPage = 8; // For Pending Maintenance
  const maxPageButtons = 10;
  // State for the loaded data file
  const [loadedDataFile, setLoadedDataFile] = useState(null); // Initialize as null or empty string
  // State for AI-predicted weekly maintenance data
  const [weeklyAIMaintenance, setWeeklyAIMaintenance] = useState([]);
  const [weeklyAILoading, setWeeklyAILoading] = useState(true);
  const [weeklyAIError, setWeeklyAIError] = useState(null);
  // States for AI Weekly Maintenance pagination
  const [aiCurrentPage, setAiCurrentPage] = useState(1);
  const aiCardsPerPage = 4; // For AI Predicted Maintenance
  const aiMaxPageButtons = 5; // Can be different or same as main pagination
  // State for the extracted location name
  const [locationName, setLocationName] = useState('');


  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        //Check sessionStorage first
        const cachedData = sessionStorage.getItem('maintenanceDashboardData');
        const cachedLoadedFile = sessionStorage.getItem('loadedDataFile'); // Check Cache for file name

        if (cachedData && cachedLoadedFile) { // Check both caches
          setDashboardData(JSON.parse(cachedData));
          setLoadedDataFile(cachedLoadedFile); // Set cached file name
          // Extract location name from cached file name
          if (cachedLoadedFile) {
            setLocationName(cachedLoadedFile.replace('.csv', ''));
          }
          setLoading(false);
          return;
        }

        //If not in cache, fetch from API
        const response = await fetch('http://localhost:8085/maintenance/dashboard');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        const smartOperationsData = data.smartOperations;
        setDashboardData(smartOperationsData);
        setLoadedDataFile(data.loaded_data_file);

        // Extract location name from fetched file name
        if (data.loaded_data_file) {
          setLocationName(data.loaded_data_file.replace('.csv', ''));
        }

        //Store data in sessionStorage for future navigations within the session
        sessionStorage.setItem('maintenanceDashboardData', JSON.stringify(smartOperationsData));
        sessionStorage.setItem('loadedDataFile', data.loaded_data_file);

      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []); // Empty dependency array ensures this runs once per component mount

  // useEffect for fetching AI-predicted weekly maintenance
  useEffect(() => {
    const fetchWeeklyAIMaintenance = async () => {
      try {
        const cachedWeeklyData = sessionStorage.getItem('weeklyAIMaintenanceData');
        if (cachedWeeklyData) {
          setWeeklyAIMaintenance(JSON.parse(cachedWeeklyData));
          setWeeklyAILoading(false);
          return;
        }

        const response = await fetch('http://localhost:8085/maintenance/upcoming-weekly-maintenance');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();

        if (data.success && Array.isArray(data.weekly_devices)) {
          setWeeklyAIMaintenance(data.weekly_devices);
          sessionStorage.setItem('weeklyAIMaintenanceData', JSON.stringify(data.weekly_devices));
        } else {
          setWeeklyAIMaintenance([]); // Ensure it's an empty array if no success or not an array
        }
      } catch (e) {
        setWeeklyAIError(e.message || 'Failed to fetch weekly AI predictions');
      } finally {
        setWeeklyAILoading(false);
      }
    };

    fetchWeeklyAIMaintenance();
  }, []); // Empty dependency array to run once on mount


  // Generate unique device names for the dropdown (for Pending Maintenance)
  const uniqueDeviceNames = useMemo(() => {
    const names = new Set();
    if (dashboardData && dashboardData.Pending_maintenance) {
      dashboardData.Pending_maintenance.forEach(item => {
        if (item.device_name) {
          names.add(item.device_name);
        }
      });
    }
    const sortedNames = Array.from(names).sort((a, b) => a.localeCompare(b));
    return sortedNames;
  }, [dashboardData]);

  // Generate unique device names for the dropdown (for AI Weekly Maintenance)
  const uniqueAIDeviceNames = useMemo(() => {
    const names = new Set();
    if (weeklyAIMaintenance) {
      weeklyAIMaintenance.forEach(item => {
        if (item.device_name) {
          names.add(item.device_name);
        }
      });
    }
    const sortedNames = Array.from(names).sort((a, b) => a.localeCompare(b));
    return sortedNames;
  }, [weeklyAIMaintenance]);

  // Filtering logic for pending maintenance cards
  const filteredMaintenance = dashboardData && dashboardData.Pending_maintenance
    ? dashboardData.Pending_maintenance.filter(item =>
      item.device_name.toLowerCase().includes(filterDeviceName.toLowerCase())
    )
    : [];

  // Filtering logic for AI Weekly Maintenance cards
  const filteredAIMaintenance = weeklyAIMaintenance
    ? weeklyAIMaintenance.filter(item =>
      item.device_name.toLowerCase().includes(aiFilterDeviceName.toLowerCase())
    )
    : [];


  // Pagination calculations for Pending Maintenance
  const indexOfLastCard = currentPage * cardsPerPage;
  const indexOfFirstCard = indexOfLastCard - cardsPerPage;
  const currentCards = filteredMaintenance.slice(indexOfFirstCard, indexOfLastCard);
  const totalPages = Math.ceil(filteredMaintenance.length / cardsPerPage);

  // Pagination calculations for AI Weekly Maintenance
  const aiIndexOfLastCard = aiCurrentPage * aiCardsPerPage;
  const aiIndexOfFirstCard = aiIndexOfLastCard - aiCardsPerPage;
  const aiCurrentCards = filteredAIMaintenance.slice(aiIndexOfFirstCard, aiIndexOfLastCard); // Use filteredAIMaintenance here
  const aiTotalPages = Math.ceil(filteredAIMaintenance.length / aiCardsPerPage); // Use filteredAIMaintenance here


  // Logic to determine which page numbers to display in the pagination controls (for Pending Maintenance)
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
  const aiVisiblePageNumbers = getVisiblePageNumbers(aiTotalPages, aiCurrentPage, aiMaxPageButtons);


  // Function to change page (for Pending Maintenance)
  const paginate = (pageNumber) => setCurrentPage(pageNumber);

  // Function to change page (for AI Weekly Maintenance)
  const paginateAI = (pageNumber) => setAiCurrentPage(pageNumber);


  // Handler for filter change, resets page to 1 (for Pending Maintenance)
  const handleFilterChange = (e) => {
    setFilterDeviceName(e.target.value);
    setCurrentPage(1); // Reset to first page when filter changes
  };

  // Handler for AI filter change, resets page to 1
  const handleAIFilterChange = (e) => {
    setAiFilterDeviceName(e.target.value);
    setAiCurrentPage(1); // Reset to first page when AI filter changes
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
      <Container fluid className="py-4 dashboard-container align-item-center">
        <p className="fs-4">Error: {error}</p>
      </Container>
    );
  }

  const handleShowDetails = async (roomNo, deviceName) => {
    setShowDetailModal(true); // Open the modal immediately
    setSelectedDeviceDetails(null); // Clear previous details
    setDetailLoading(true);
    setDetailError(null);

    try {
      // Construct the URL using template literals
      const apiUrl = `http://localhost:8085/maintenance/device/info?room_no=${roomNo}&appliance_type=${deviceName}`;
      const response = await fetch(apiUrl);

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      setSelectedDeviceDetails(data); // Set the fetched details
    } catch (e) {
      setDetailError(e.message);
    } finally {
      setDetailLoading(false);
    }
  };

  const handleCloseDetails = () => {
    setShowDetailModal(false);
    setSelectedDeviceDetails(null); // Clear details when closing
    setDetailError(null); // Clear any errors
  };

  // Define the main cards based on the fetched data
  const mainCards = dashboardData ? [
    {
      id: 'total_devices',
      title: 'Total Devices',
      value: dashboardData.total_devices,
      icon: <MdDevicesOther />,
      variant: 'primary',
      description: 'Total number of devices.',
    },
    {
      id: 'running',
      title: 'Running Devices',
      value: dashboardData.running,
      icon: <FaCheckCircle />,
      variant: 'success',
      description: 'Devices currently operational.',
    },
    {
      id: 'down',
      title: 'Non-Operational',
      value: dashboardData.down,
      icon: <FaExclamationTriangle />,
      variant: 'danger',
      description: 'Devices not working.',
    },
    {
      id: 'due_maintenance',
      title: 'Due for Maintenance',
      value: dashboardData.due_maintenance,
      icon: <FaTools />,
      variant: 'warning',
      description: 'Devices needing upcoming maintenance.',
    },
  ] : [];


  return (
    <>
      {/* Pass the loadedDataFile to the SystemStatusBanner */}
      {/* Conditionally render the banner only if loadedDataFile is available */}
      {loadedDataFile && <SystemStatusBanner loadedDataFile={loadedDataFile} />}

      <Container fluid className="py-4 dashboard-container">
        {/* Dashboard Title */}
        <h3 className="text-center mb-4 text-light">
          {locationName ? `${locationName} Maintenance Dashboard` : 'Maintenance Dashboard'}
        </h3>

        {/* Main Statistics Cards */}
        <Row className="justify-content-center g-4 mb-5">
          {mainCards.map((card) => (
            <Col key={card.id} xs={12} sm={6} md={4} lg={3}>
              <Card bg={card.variant} text="white" className="shadow-lg h-100 rounded">
                <Card.Body className="d-flex flex-column justify-content-between">
                  <div className="d-flex align-items-center mb-3">
                    <div className="me-3 fs-2">{card.icon}</div>
                    <Card.Title className="mb-0 fs-5">{card.title}</Card.Title>
                  </div>
                  <Card.Text className="display-4 fw-bold">{card.value}</Card.Text>
                  <Card.Text><small>{card.description}</small></Card.Text>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>

        {/* AI-Predicted Maintenance Next Week Section */}
        <h3 className="text-center mb-4 mt-5 text-light">AI-Predicted Maintenance For This Week</h3>
        {/* Dropdown Filter for AI-Predicted Maintenance */}
        <Row className="justify-content-center mb-4">
          <Col xs={12} md={6} lg={4}>
            <Form.Select
              aria-label="Filter AI by device name"
              value={aiFilterDeviceName}
              onChange={handleAIFilterChange}
              className="bg-light text-dark border-secondary"
            >
              <option value="">All Devices</option>
              {uniqueAIDeviceNames.map((name, index) => (
                <option key={`ai-${index}`} value={name}>{name}</option>
              ))}
            </Form.Select>
          </Col>
        </Row>

        {weeklyAILoading ? (
          <Container fluid className="d-flex justify-content-center align-items-center" style={{ minHeight: '100px' }}>
            <Spinner animation="border" role="status" className="text-info">
              <span className="visually-hidden">Loading AI predictions...</span>
            </Spinner>
            <p className='text-info ms-2'>Loading AI predictions...</p>
          </Container>
        ) : weeklyAIError ? (
          <Col xs={12}>
            <p className="text-center text-danger fs-5">Error loading AI predictions: {weeklyAIError}</p>
          </Col>
        ) : aiCurrentCards.length > 0 ? (
          <>
            <Row className="justify-content-center g-4">
              {aiCurrentCards.map((device, index) => (
                <Col key={device.device_id || index} xs={12} sm={6} md={4} lg={3}>
                  <Card className="ai-prediction-card shadow-lg h-100 rounded">
                    <Card.Body className="d-flex flex-column justify-content-between">
                      <div className="d-flex align-items-center mb-3">
                        <div className="me-3 fs-2 text-primary"><RiAiGenerate2 /></div>
                        <Card.Title className="mb-0 fs-5">{device.device_name}</Card.Title>
                      </div>
                      <Card.Text className="fs-6 text-dark">
                        <strong>Room No:</strong> {device.room_no}<br />
                        <strong>Predicted Maintenance Date:</strong> <span className="fw-bold text-success">{device.next_maintenance_date}</span>
                      </Card.Text>
                      <div className="text-end mt-2">
                        <span className="badge bg-primary text-white ai-badge">AI-Powered Prediction</span>
                      </div>
                    </Card.Body>
                  </Card>
                </Col>
              ))}
            </Row>

            {/* Pagination Controls for AI Weekly Maintenance */}
            {aiTotalPages > 1 && (
              <Row className="justify-content-center mt-4">
                <Col xs="auto">
                  <Pagination className="custom-pagination">
                    <Pagination.First onClick={() => paginateAI(1)} disabled={aiCurrentPage === 1} />
                    <Pagination.Prev onClick={() => paginateAI(aiCurrentPage - 1)} disabled={aiCurrentPage === 1} />

                    {aiVisiblePageNumbers[0] > 1 && <Pagination.Ellipsis />}

                    {aiVisiblePageNumbers.map((pageNumber) => (
                      <Pagination.Item
                        key={`ai-page-${pageNumber}`}
                        active={pageNumber === aiCurrentPage}
                        onClick={() => paginateAI(pageNumber)}
                      >
                        {pageNumber}
                      </Pagination.Item>
                    ))}

                    {aiVisiblePageNumbers[aiVisiblePageNumbers.length - 1] < aiTotalPages && <Pagination.Ellipsis />}

                    <Pagination.Next onClick={() => paginateAI(aiCurrentPage + 1)} disabled={aiCurrentPage === aiTotalPages} />
                    <Pagination.Last onClick={() => paginateAI(aiTotalPages)} disabled={aiCurrentPage === aiTotalPages} />
                  </Pagination>
                </Col>
              </Row>
            )}
          </>
        ) : (
          <Col xs={12}>
            <p className="text-center text-secondary fs-5">
              {aiFilterDeviceName ? `No AI-predicted maintenance for "${aiFilterDeviceName}" devices this week.` : 'No AI-predicted maintenance needed next 7 days.'}
            </p>
          </Col>
        )}


        {/* Pending Maintenance Section */}
        <h3 className="text-center mb-4 mt-5 text-light">Pending Maintenance</h3>
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

        {/* Pending Maintenance Cards (filtered) */}
        <Row className="justify-content-center g-4">
          {currentCards.length > 0 ? (
            currentCards.map((item, index) => (
              <Col key={item.device_name + item.room_no + index} xs={12} sm={6} md={4} lg={3}>
                <Card bg="secondary" text="white" className="shadow-lg h-100 rounded">
                  <Card.Body className="d-flex flex-column justify-content-between">
                    <div className="d-flex align-items-center mb-3">
                      <div className="me-3 fs-2 text-warning"></div>
                      <Card.Title className="mb-0 fs-5">{item.device_name}</Card.Title>
                    </div>
                    <Card.Text className="fs-6">
                      <strong>Room No:</strong> {item.room_no}<br />
                      <strong>Maintenance Due:</strong> {item.maintenance_date}
                    </Card.Text>
                    <Button
                      variant="light"
                      className="mt-3"
                      onClick={() => handleShowDetails(item.room_no, item.device_name)}>
                      More Details...
                    </Button>
                  </Card.Body>
                </Card>
              </Col>
            ))
          ) : (
            <Col xs={12}>
              <p className="text-center text-secondary fs-5">
                {filterDeviceName ? `No "${filterDeviceName}" devices found for maintenance.` : 'No pending maintenance items.'}
              </p>
            </Col>
          )}
        </Row>

        {/* Pagination Controls for Pending Maintenance */}
        {totalPages > 1 && (
          <Row className="justify-content-center mt-4">
            <Col xs="auto">
              <Pagination className="custom-pagination">
                <Pagination.First onClick={() => paginate(1)} disabled={currentPage === 1} />
                <Pagination.Prev onClick={() => paginate(currentPage - 1)} disabled={currentPage === 1} />

                {visiblePageNumbers[0] > 1 && <Pagination.Ellipsis />}

                {visiblePageNumbers.map((pageNumber) => (
                  <Pagination.Item
                    key={pageNumber}
                    active={pageNumber === currentPage}
                    onClick={() => paginate(pageNumber)}
                  >
                    {pageNumber}
                  </Pagination.Item>
                ))}

                {visiblePageNumbers[visiblePageNumbers.length - 1] < totalPages && <Pagination.Ellipsis />}

                <Pagination.Next onClick={() => paginate(currentPage + 1)} disabled={currentPage === totalPages} />
                <Pagination.Last onClick={() => paginate(totalPages)} disabled={currentPage === totalPages} />
              </Pagination>
            </Col>
          </Row>
        )}

      </Container>

      <Modal show={showDetailModal} onHide={handleCloseDetails} centered>
        <Modal.Header closeButton>
          <Modal.Title>Device Details</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {detailLoading && <p>Loading device details...</p>}
          {detailError && <p className="text-danger">Error: {detailError}</p>}
          {selectedDeviceDetails && (
            <div className="text-dark">
              <p><strong>Device Name:</strong> {selectedDeviceDetails.device_name}</p>
              <p><strong>Room No:</strong> {selectedDeviceDetails.room_no}</p>
              <p><strong>Device Year:</strong> {selectedDeviceDetails.device_year}</p>
              <p><strong>Issue Reported:</strong> {selectedDeviceDetails.issue_reported || 'N/A'}</p>
              <p><strong>Next Maintenance Date:</strong> {selectedDeviceDetails.next_maintenance_date}</p>
              <p><strong>Previous Maintenance Date:</strong> {selectedDeviceDetails.previous_maintenance_date || 'N/A'}</p>
              <p><strong>Under Warranty:</strong> {selectedDeviceDetails.under_warranty}</p>
              <p><strong>Warranty Year Till:</strong> {selectedDeviceDetails.warranty_year_till || 'N/A'}</p>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={handleCloseDetails}>
            Close
          </Button>
        </Modal.Footer>
      </Modal>
    </>
  );
}

export default Dashboard;