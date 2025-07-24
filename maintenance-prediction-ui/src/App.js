import './App.css';
import 'bootstrap/dist/css/bootstrap.min.css';
import './styles/styles.css';
import { BrowserRouter as Router, Route, Routes } from 'react-router-dom';
import MyNavbar from './components/MyNavbar'; 
import Dashboard from './components/Dashboard';
import Scheduled from './components/Scheduled';
import Upcoming from './components/Upcoming';
import RoomSearch from './components/RoomSearch';

function App() {
  // SystemStatusBanner height.
  const BANNER_HEIGHT = '0px';
  const NAVBAR_HEIGHT = '0px'; // Adjust this value AFTER measuring

  const TOTAL_HEADER_HEIGHT = `calc(${BANNER_HEIGHT} + ${NAVBAR_HEIGHT})`;

  return (
    <Router>
      <MyNavbar/>
      {/* Main content area - pushed down by the combined height */}
      <main style={{ paddingTop: TOTAL_HEADER_HEIGHT }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/scheduled-maintenance" element={<Scheduled />} />
          <Route path="/upcoming-maintenance" element={<Upcoming />} />
          <Route path="/room-search-results" element={<RoomSearch />} />
        </Routes>
      </main>
    </Router>
  );
}

export default App;