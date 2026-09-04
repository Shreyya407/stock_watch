import React, { useState, useEffect, useMemo } from 'react';
import { Search, X, Plus, Check, Loader2, AlertCircle, Sparkles, Building2 } from 'lucide-react';
import { api } from '../services/api';
import { useWatchlist } from '../context/WatchlistContext';

// Client-side fallback registry ensuring search ALWAYS works instantly with 118+ top Indian equities
const FALLBACK_POPULAR_STOCKS = [
  { symbol: "RELIANCE", name: "Reliance Industries Ltd", sector: "Energy / Oil & Gas", exchange: "NSE" },
  { symbol: "TCS", name: "Tata Consultancy Services Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "HDFCBANK", name: "HDFC Bank Ltd", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "INFY", name: "Infosys Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "ICICIBANK", name: "ICICI Bank Ltd", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "BHARTIARTL", name: "Bharti Airtel Ltd", sector: "Telecommunications", exchange: "NSE" },
  { symbol: "SBIN", name: "State Bank of India", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "ITC", name: "ITC Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "LT", name: "Larsen & Toubro Ltd", sector: "Capital Goods & Construction", exchange: "NSE" },
  { symbol: "TATAMOTORS", name: "Tata Motors Ltd", sector: "Automobile", exchange: "NSE" },
  { symbol: "HINDUNILVR", name: "Hindustan Unilever Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "BAJFINANCE", name: "Bajaj Finance Ltd", sector: "Financial Services", exchange: "NSE" },
  { symbol: "KOTAKBANK", name: "Kotak Mahindra Bank Ltd", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "AXISBANK", name: "Axis Bank Ltd", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "ASIANPAINT", name: "Asian Paints Ltd", sector: "Consumer Durables", exchange: "NSE" },
  { symbol: "MARUTI", name: "Maruti Suzuki India Ltd", sector: "Automobile", exchange: "NSE" },
  { symbol: "SUNPHARMA", name: "Sun Pharmaceutical Industries Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "TITAN", name: "Titan Company Ltd", sector: "Consumer Durables", exchange: "NSE" },
  { symbol: "WIPRO", name: "Wipro Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "HCLTECH", name: "HCL Technologies Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "NTPC", name: "NTPC Ltd", sector: "Power / Utilities", exchange: "NSE" },
  { symbol: "ONGC", name: "Oil and Natural Gas Corporation Ltd", sector: "Energy / Oil & Gas", exchange: "NSE" },
  { symbol: "POWERGRID", name: "Power Grid Corporation of India Ltd", sector: "Power / Utilities", exchange: "NSE" },
  { symbol: "ULTRACEMCO", name: "UltraTech Cement Ltd", sector: "Materials / Cement", exchange: "NSE" },
  { symbol: "JSWSTEEL", name: "JSW Steel Ltd", sector: "Metals & Mining", exchange: "NSE" },
  { symbol: "TATASTEEL", name: "Tata Steel Ltd", sector: "Metals & Mining", exchange: "NSE" },
  { symbol: "ADANIENT", name: "Adani Enterprises Ltd", sector: "Conglomerate", exchange: "NSE" },
  { symbol: "ADANIPORTS", name: "Adani Ports and Special Economic Zone Ltd", sector: "Infrastructure", exchange: "NSE" },
  { symbol: "COALINDIA", name: "Coal India Ltd", sector: "Metals & Mining", exchange: "NSE" },
  { symbol: "BAJAJFINSV", name: "Bajaj Finserv Ltd", sector: "Financial Services", exchange: "NSE" },
  { symbol: "M&M", name: "Mahindra & Mahindra Ltd", sector: "Automobile", exchange: "NSE" },
  { symbol: "NESTLEIND", name: "Nestle India Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "BRITANNIA", name: "Britannia Industries Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "TATACONSUM", name: "Tata Consumer Products Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "GRASIM", name: "Grasim Industries Ltd", sector: "Materials", exchange: "NSE" },
  { symbol: "HINDALCO", name: "Hindalco Industries Ltd", sector: "Metals & Mining", exchange: "NSE" },
  { symbol: "VEDL", name: "Vedanta Ltd", sector: "Metals & Mining", exchange: "NSE" },
  { symbol: "DIVISLAB", name: "Divi's Laboratories Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "DRREDDY", name: "Dr. Reddy's Laboratories Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "CIPLA", name: "Cipla Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "EICHERMOT", name: "Eicher Motors Ltd", sector: "Automobile", exchange: "NSE" },
  { symbol: "HEROMOTOCO", name: "Hero MotoCorp Ltd", sector: "Automobile", exchange: "NSE" },
  { symbol: "BAJAJ-AUTO", name: "Bajaj Auto Ltd", sector: "Automobile", exchange: "NSE" },
  { symbol: "TVSMOTOR", name: "TVS Motor Company Ltd", sector: "Automobile", exchange: "NSE" },
  { symbol: "TECHM", name: "Tech Mahindra Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "LTIM", name: "LTIMindtree Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "PERSISTENT", name: "Persistent Systems Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "COFORGE", name: "Coforge Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "KPITTECH", name: "KPIT Technologies Ltd", sector: "Automotive Tech / IT", exchange: "NSE" },
  { symbol: "TATAELXSI", name: "Tata Elxsi Ltd", sector: "Information Technology", exchange: "NSE" },
  { symbol: "BEL", name: "Bharat Electronics Ltd", sector: "Aerospace & Defence", exchange: "NSE" },
  { symbol: "HAL", name: "Hindustan Aeronautics Ltd", sector: "Aerospace & Defence", exchange: "NSE" },
  { symbol: "BHEL", name: "Bharat Heavy Electricals Ltd", sector: "Capital Goods", exchange: "NSE" },
  { symbol: "MAZDOCK", name: "Mazagon Dock Shipbuilders Ltd", sector: "Defence & Shipbuilding", exchange: "NSE" },
  { symbol: "COCHINSHIP", name: "Cochin Shipyard Ltd", sector: "Defence & Shipbuilding", exchange: "NSE" },
  { symbol: "BDL", name: "Bharat Dynamics Ltd", sector: "Aerospace & Defence", exchange: "NSE" },
  { symbol: "ZOMATO", name: "Zomato Ltd", sector: "Consumer Tech / Food Delivery", exchange: "NSE" },
  { symbol: "JIOFIN", name: "Jio Financial Services Ltd", sector: "Financial Services", exchange: "NSE" },
  { symbol: "PAYTM", name: "One 97 Communications (Paytm)", sector: "Fintech", exchange: "NSE" },
  { symbol: "NYKAA", name: "FSN E-Commerce Ventures (Nykaa)", sector: "Consumer Tech / Retail", exchange: "NSE" },
  { symbol: "POLICYBZR", name: "PB Fintech (Policybazaar)", sector: "Fintech / Insurtech", exchange: "NSE" },
  { symbol: "DELHIVERY", name: "Delhivery Ltd", sector: "Logistics & Supply Chain", exchange: "NSE" },
  { symbol: "NAUKRI", name: "Info Edge (India) Ltd", sector: "Internet / Recruitment", exchange: "NSE" },
  { symbol: "IRCTC", name: "Indian Railway Catering and Tourism Corp", sector: "Services & Travel", exchange: "NSE" },
  { symbol: "INDIGO", name: "InterGlobe Aviation (IndiGo)", sector: "Aviation", exchange: "NSE" },
  { symbol: "TRENT", name: "Trent Ltd (Westside / Zudio)", sector: "Retail & Fashion", exchange: "NSE" },
  { symbol: "DMART", name: "Avenue Supermarts (DMart)", sector: "Retail", exchange: "NSE" },
  { symbol: "VBL", name: "Varun Beverages Ltd", sector: "Consumer Goods (Beverages)", exchange: "NSE" },
  { symbol: "DABUR", name: "Dabur India Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "MARICO", name: "Marico Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "GODREJCP", name: "Godrej Consumer Products Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "COLPAL", name: "Colgate-Palmolive (India) Ltd", sector: "Consumer Goods (FMCG)", exchange: "NSE" },
  { symbol: "TATAPOWER", name: "Tata Power Company Ltd", sector: "Power / Renewable Energy", exchange: "NSE" },
  { symbol: "ADANIGREEN", name: "Adani Green Energy Ltd", sector: "Renewable Energy", exchange: "NSE" },
  { symbol: "ADANIPOWER", name: "Adani Power Ltd", sector: "Power / Utilities", exchange: "NSE" },
  { symbol: "SUZLON", name: "Suzlon Energy Ltd", sector: "Renewable Energy / Wind", exchange: "NSE" },
  { symbol: "IREDA", name: "Indian Renewable Energy Development Agency", sector: "Financial Services", exchange: "NSE" },
  { symbol: "NHPC", name: "NHPC Ltd", sector: "Power / Hydro", exchange: "NSE" },
  { symbol: "BPCL", name: "Bharat Petroleum Corporation Ltd", sector: "Energy / Oil & Gas", exchange: "NSE" },
  { symbol: "IOC", name: "Indian Oil Corporation Ltd", sector: "Energy / Oil & Gas", exchange: "NSE" },
  { symbol: "GAIL", name: "GAIL (India) Ltd", sector: "Energy / Gas Transmission", exchange: "NSE" },
  { symbol: "APOLLOHOSP", name: "Apollo Hospitals Enterprise Ltd", sector: "Healthcare & Hospitals", exchange: "NSE" },
  { symbol: "MANKIND", name: "Mankind Pharma Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "MAXHEALTH", name: "Max Healthcare Institute Ltd", sector: "Healthcare & Hospitals", exchange: "NSE" },
  { symbol: "LUPIN", name: "Lupin Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "AUROPHARMA", name: "Aurobindo Pharma Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "TORNTPHARM", name: "Torrent Pharmaceuticals Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "ZYDUSLIFE", name: "Zydus Lifesciences Ltd", sector: "Healthcare & Pharma", exchange: "NSE" },
  { symbol: "BIOCON", name: "Biocon Ltd", sector: "Biotechnology & Pharma", exchange: "NSE" },
  { symbol: "DLF", name: "DLF Ltd", sector: "Real Estate", exchange: "NSE" },
  { symbol: "GODREJPROP", name: "Godrej Properties Ltd", sector: "Real Estate", exchange: "NSE" },
  { symbol: "LODHA", name: "Macrotech Developers (Lodha)", sector: "Real Estate", exchange: "NSE" },
  { symbol: "OBEROIRLTY", name: "Oberoi Realty Ltd", sector: "Real Estate", exchange: "NSE" },
  { symbol: "PRESTIGE", name: "Prestige Estates Projects Ltd", sector: "Real Estate", exchange: "NSE" },
  { symbol: "PIDILITIND", name: "Pidilite Industries Ltd (Fevicol)", sector: "Chemicals", exchange: "NSE" },
  { symbol: "BERGEPAINT", name: "Berger Paints India Ltd", sector: "Consumer Durables", exchange: "NSE" },
  { symbol: "HAVELLS", name: "Havells India Ltd", sector: "Consumer Electricals", exchange: "NSE" },
  { symbol: "POLYCAB", name: "Polycab India Ltd", sector: "Cables & Electricals", exchange: "NSE" },
  { symbol: "KEI", name: "KEI Industries Ltd", sector: "Cables & Electricals", exchange: "NSE" },
  { symbol: "SIEMENS", name: "Siemens Ltd", sector: "Capital Goods / Engineering", exchange: "NSE" },
  { symbol: "ABB", name: "ABB India Ltd", sector: "Capital Goods / Engineering", exchange: "NSE" },
  { symbol: "AMBUJACEM", name: "Ambuja Cements Ltd", sector: "Materials / Cement", exchange: "NSE" },
  { symbol: "ACC", name: "ACC Ltd", sector: "Materials / Cement", exchange: "NSE" },
  { symbol: "SHREECEM", name: "Shree Cement Ltd", sector: "Materials / Cement", exchange: "NSE" },
  { symbol: "MUTHOOTFIN", name: "Muthoot Finance Ltd", sector: "Financial Services / Gold Loan", exchange: "NSE" },
  { symbol: "CHOLAFIN", name: "Cholamandalam Investment & Finance", sector: "Financial Services", exchange: "NSE" },
  { symbol: "SHRIRAMFIN", name: "Shriram Finance Ltd", sector: "Financial Services", exchange: "NSE" },
  { symbol: "HDFCLIFE", name: "HDFC Life Insurance Company Ltd", sector: "Insurance", exchange: "NSE" },
  { symbol: "SBILIFE", name: "SBI Life Insurance Company Ltd", sector: "Insurance", exchange: "NSE" },
  { symbol: "ICICIPRULI", name: "ICICI Prudential Life Insurance", sector: "Insurance", exchange: "NSE" },
  { symbol: "BANKBARODA", name: "Bank of Baroda", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "PNB", name: "Punjab National Bank", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "CANBK", name: "Canara Bank", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "INDUSINDBK", name: "IndusInd Bank Ltd", sector: "Banking & Financial Services", exchange: "NSE" },
  { symbol: "JINDALSTEL", name: "Jindal Steel & Power Ltd", sector: "Metals & Mining", exchange: "NSE" },
  { symbol: "NMDC", name: "NMDC Ltd", sector: "Metals & Mining", exchange: "NSE" },
  { symbol: "NATIONALUM", name: "National Aluminium Company Ltd", sector: "Metals & Mining", exchange: "NSE" },
  { symbol: "SAIL", name: "Steel Authority of India Ltd", sector: "Metals & Mining", exchange: "NSE" },
];

const SECTORS = ['All', 'Banking', 'IT', 'Auto', 'FMCG', 'Pharma', 'Energy', 'Metals', 'Defence', 'Retail', 'Real Estate'];

export const AddStockModal = () => {
  const { isAddModalOpen, setIsAddModalOpen, addStock, stocks: currentWatchlist } = useWatchlist();
  const [query, setQuery] = useState('');
  const [selectedSector, setSelectedSector] = useState('All');
  const [allStocks, setAllStocks] = useState(FALLBACK_POPULAR_STOCKS);
  const [searching, setSearching] = useState(false);
  const [addingSymbol, setAddingSymbol] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);
  const [successSymbol, setSuccessSymbol] = useState(null);

  // Load all stocks from backend on modal open
  useEffect(() => {
    if (!isAddModalOpen) return;

    let isMounted = true;
    const fetchAll = async () => {
      setSearching(true);
      setErrorMessage(null);
      try {
        const data = await api.searchStocks('');
        if (isMounted && data && Array.isArray(data) && data.length > 0) {
          setAllStocks(data);
        }
      } catch (err) {
        console.warn('Using local popular stocks registry fallback:', err);
        // Fallback is already initialized in state
      } finally {
        if (isMounted) setSearching(false);
      }
    };

    fetchAll();
  }, [isAddModalOpen]);

  // Client-side instant filter across all companies, query, and sector
  const filteredResults = useMemo(() => {
    const q = (query || '').trim().toLowerCase();
    return allStocks.filter(item => {
      // Sector filter
      if (selectedSector !== 'All') {
        const itemSec = (item.sector || '').toLowerCase();
        const secMatch = selectedSector.toLowerCase();
        if (!itemSec.includes(secMatch)) return false;
      }

      // Query filter
      if (!q) return true;
      return (
        item.symbol.toLowerCase().includes(q) ||
        item.name.toLowerCase().includes(q) ||
        (item.sector && item.sector.toLowerCase().includes(q))
      );
    });
  }, [allStocks, query, selectedSector]);

  if (!isAddModalOpen) return null;

  const handleSelect = async (symbol) => {
    setAddingSymbol(symbol);
    setErrorMessage(null);
    setSuccessSymbol(null);

    const res = await addStock(symbol);
    setAddingSymbol(null);

    if (res.success) {
      setSuccessSymbol(symbol);
      setTimeout(() => {
        setIsAddModalOpen(false);
        setSuccessSymbol(null);
        setQuery('');
      }, 700);
    } else {
      setErrorMessage(res.error || 'Failed to add stock to watchlist.');
    }
  };

  const isAlreadyInWatchlist = (symbol) => {
    return (currentWatchlist || []).some(s => s.symbol === symbol);
  };

  return (
    <div className="modal-backdrop" onClick={() => setIsAddModalOpen(false)}>
      <div className="modal-card" style={{ maxWidth: '640px', width: '95%' }} onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: 'var(--radius-md)',
              background: 'var(--accent-subtle)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent-primary)',
            }}>
              <Building2 size={20} />
            </div>
            <div>
              <h3 className="modal-title">Add Stock to Watchlist</h3>
              <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                Explore 100+ Real-time NSE Indian Equities
              </span>
            </div>
          </div>
          <button
            onClick={() => setIsAddModalOpen(false)}
            className="icon-btn"
            aria-label="Close add stock modal"
          >
            <X size={18} />
          </button>
        </div>

        <div className="modal-body" style={{ gap: '14px', maxHeight: '68vh', overflowY: 'auto' }}>
          {/* Search Bar */}
          <div className="search-input-wrap">
            <Search size={18} className="search-icon-pos" />
            <input
              type="text"
              className="search-input"
              placeholder="Search by symbol or company name (e.g. TCS, Reliance, Zomato, Tata)..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              autoFocus
            />
            {query && (
              <button
                type="button"
                onClick={() => setQuery('')}
                className="icon-btn"
                style={{ position: 'absolute', right: '10px', top: '50%', transform: 'translateY(-50%)', padding: '4px' }}
                aria-label="Clear search"
              >
                <X size={14} />
              </button>
            )}
          </div>

          {/* Sector Category Pills */}
          <div style={{
            display: 'flex',
            gap: '6px',
            overflowX: 'auto',
            paddingBottom: '4px',
            scrollbarWidth: 'none',
          }}>
            {SECTORS.map((sec) => (
              <button
                key={sec}
                type="button"
                onClick={() => setSelectedSector(sec)}
                style={{
                  padding: '5px 12px',
                  borderRadius: '20px',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                  border: '1px solid',
                  transition: 'all 0.15s ease',
                  background: selectedSector === sec ? 'var(--accent-primary)' : 'var(--surface-primary)',
                  color: selectedSector === sec ? '#ffffff' : 'var(--text-secondary)',
                  borderColor: selectedSector === sec ? 'var(--accent-primary)' : 'var(--border-color)',
                }}
              >
                {sec}
              </button>
            ))}
          </div>

          {errorMessage && (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 14px',
              background: 'var(--sig-subtle)',
              border: '1px solid var(--sig-border)',
              borderRadius: 'var(--radius-md)',
              color: 'var(--sig-color)',
              fontSize: '0.82rem'
            }}>
              <AlertCircle size={15} />
              <span>{errorMessage}</span>
            </div>
          )}

          {/* Results Header */}
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <span style={{ fontSize: '0.72rem', textTransform: 'uppercase', color: 'var(--text-muted)', fontWeight: 600, letterSpacing: '0.05em' }}>
              {query ? `Matching Equities (${filteredResults.length})` : `All Listed Indian Equities (${filteredResults.length})`}
            </span>
            <span style={{ fontSize: '0.72rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
              Live NSE Market Quotes
            </span>
          </div>

          {/* Companies List */}
          {searching ? (
            <div style={{ padding: '36px', display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', color: 'var(--text-muted)' }}>
              <Loader2 size={26} className="animate-spin text-accent" />
              <span style={{ fontSize: '0.82rem' }}>Loading Indian equities directory...</span>
            </div>
          ) : filteredResults.length === 0 ? (
            <div style={{ padding: '30px', textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
              <p>No matching NSE equities found for "{query}".</p>
            </div>
          ) : (
            <div className="search-results-list" style={{ maxHeight: '380px', overflowY: 'auto' }}>
              {filteredResults.map((item) => {
                const isAdding = addingSymbol === item.symbol;
                const isAdded = successSymbol === item.symbol;
                const inWatchlist = isAlreadyInWatchlist(item.symbol);

                return (
                  <div
                    key={item.symbol}
                    className="search-result-item"
                    onClick={() => !isAdding && !inWatchlist && handleSelect(item.symbol)}
                    style={{
                      cursor: inWatchlist ? 'default' : 'pointer',
                      opacity: inWatchlist ? 0.75 : 1,
                    }}
                  >
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '2px' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontFamily: 'var(--font-heading)', fontWeight: 700, fontSize: '0.96rem' }}>
                          {item.symbol}
                        </span>
                        <span style={{ fontSize: '0.68rem', background: 'var(--surface-primary)', padding: '2px 6px', borderRadius: '4px', border: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                          {item.exchange || 'NSE'}
                        </span>
                      </div>
                      <span style={{ fontSize: '0.78rem', color: 'var(--text-secondary)' }}>
                        {item.name} {item.sector ? `• ${item.sector}` : ''}
                      </span>
                    </div>

                    <button
                      className={isAdded || inWatchlist ? 'btn-secondary' : 'btn-primary'}
                      style={{
                        padding: '6px 14px',
                        fontSize: '0.78rem',
                        display: 'flex',
                        alignItems: 'center',
                        gap: '6px',
                        borderRadius: 'var(--radius-md)',
                      }}
                      disabled={isAdding || inWatchlist}
                      onClick={(e) => {
                        e.stopPropagation();
                        if (!inWatchlist) handleSelect(item.symbol);
                      }}
                    >
                      {isAdding ? (
                        <Loader2 size={13} className="animate-spin" />
                      ) : inWatchlist ? (
                        <>
                          <Check size={13} style={{ color: 'var(--accent-primary)' }} />
                          <span style={{ color: 'var(--text-secondary)' }}>In Watchlist</span>
                        </>
                      ) : isAdded ? (
                        <>
                          <Check size={13} />
                          <span>Added!</span>
                        </>
                      ) : (
                        <>
                          <Plus size={13} />
                          <span>Add</span>
                        </>
                      )}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
          <span style={{ fontSize: '0.76rem', color: 'var(--text-muted)' }}>
            Tip: Filter by sector above or type any NSE stock symbol
          </span>
          <button
            onClick={() => setIsAddModalOpen(false)}
            className="btn-secondary"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};
