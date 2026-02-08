import type { FC } from "react";
import "./LandingPage.css";
import logo from "../assets/logo.png";

interface LandingPageProps {
  onGetStarted: () => void;
}

const LandingPage: FC<LandingPageProps> = ({ onGetStarted }) => {
  return (
    <div className="landing-page">
      <header className="landing-header">
        <div className="landing-logo">
          <img src={logo} alt="BinSight Logo" className="logo-image" />
          <span className="logo-text">BinSight</span>
        </div>
      </header>

      <main className="landing-hero">
        <div className="hero-content">
          <h1 className="hero-headline">
            <span className="headline-bold">Smart Collection</span>
            <br />
            <span className="headline-light">for Modern Cities</span>
          </h1>
          <p className="hero-subheading">
            Real-time bin monitoring and intelligent route optimization powered
            by IoT sensors. Reduce emissions, cut costs, and keep cities
            cleaner.
          </p>
          <button className="cta-primary" onClick={onGetStarted}>
            Get Started
            <span className="cta-arrow">→</span>
          </button>
        </div>

        <div className="hero-visual">
          <div className="dashboard-mockup">
            <div className="mockup-sidebar">
              <div className="mockup-bin critical"></div>
              <div className="mockup-bin medium"></div>
              <div className="mockup-bin low"></div>
            </div>
            <div className="mockup-map">
              <div className="mockup-marker marker-1"></div>
              <div className="mockup-marker marker-2"></div>
              <div className="mockup-marker marker-3"></div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
};

export default LandingPage;
