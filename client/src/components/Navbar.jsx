import { Link } from 'react-router-dom'
import './Navbar.css'

export default function Navbar() {
  return (
    <header className="navbar">
      <div className="container navbar__inner">
        <Link to="/" className="navbar__brand">
          <span className="navbar__dot" />
          Prepline
        </Link>
        <nav className="navbar__links">
          <a href="#how-it-works">How it works</a>
          <a href="#about">About</a>
          <button className="navbar__login">Log in</button>
        </nav>
      </div>
    </header>
  )
}
