import DashboardLayout from "../components/DashboardLayout"
import { useEffect, useState, useRef } from "react"
import { useNavigate } from "react-router-dom"

function Dashboard() {
  const [user, setUser] = useState({})
  const [currentTime, setCurrentTime] = useState(new Date())
  const [dropdownOpen, setDropdownOpen] = useState(false)
  const navigate = useNavigate()
  const dropdownRef = useRef()

  useEffect(() => {
    const savedUser = JSON.parse(localStorage.getItem("user"))
    if (savedUser) setUser(savedUser)

    // Update time every minute
    const timer = setInterval(() => {
      setCurrentTime(new Date())
    }, 60000)

    return () => clearInterval(timer)
  }, [])

  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setDropdownOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => document.removeEventListener("mousedown", handleClickOutside)
  }, [])

  const formatTime = (date) => {
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      hour12: true,
    })
  }

  const formatDate = (date) => {
    return date.toLocaleDateString("en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    })
  }

  const quickActions = [
    {
      title: "Generate New Architecture",
      description: "Create AWS architecture from your code",
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
          />
        </svg>
      ),
      link: "/generate",
      color: "from-blue-500 to-blue-600",
      hoverColor: "hover:from-blue-600 hover:to-blue-700",
      shadowColor: "shadow-blue-200",
    },
    {
      title: "Optimize Architecture",
      description: "Improve existing infrastructure",
      icon: (
        <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
      link: "/optimize",
      color: "from-purple-500 to-purple-600",
      hoverColor: "hover:from-purple-600 hover:to-purple-700",
      shadowColor: "shadow-purple-200",
    },
  ]

  const handleLogout = () => {
    localStorage.removeItem("token")
    localStorage.removeItem("user")
    navigate("/login")
  }

  return (
    <DashboardLayout>
      <div className="h-screen flex flex-col overflow-hidden">
        {/* Top Navigation Bar */}
        <header className="bg-white/80 backdrop-blur-sm shadow-lg border-b border-gray-200/50 flex-shrink-0">
          <div className="max-w-7xl mx-auto px-6 py-3">
            <div className="flex items-center justify-between">
              {/* Logo Section */}
              <div className="flex items-center space-x-3">
                <div className="p-2 bg-gradient-to-r from-blue-500 to-purple-500 rounded-xl shadow-lg">
                  <svg className="h-7 w-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z"
                    />
                  </svg>
                </div>
                <div>
                  <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                    CloudGen.AI
                  </h1>
                  <p className="text-xs text-gray-500">Architecture Intelligence</p>
                </div>
              </div>

              {/* Welcome Message */}
              <div className="hidden md:flex flex-col items-center">
                <span className="text-lg font-semibold text-gray-800">
                  Welcome back, <span className="text-blue-600">{user.name || "User"}</span>! 👋
                </span>
                <span className="text-sm text-gray-500">Ready to build amazing architectures?</span>
              </div>

              {/* Time & User Section */}
              <div className="flex items-center space-x-4">
                {/* Time Display */}
                <div className="hidden lg:block text-right bg-gradient-to-r from-gray-50 to-blue-50 px-3 py-2 rounded-lg border border-gray-200">
                  <div className="text-sm font-bold text-gray-900">{formatTime(currentTime)}</div>
                  <div className="text-xs text-gray-500">{formatDate(currentTime)}</div>
                </div>

                {/* User Dropdown */}
                <div className="relative" ref={dropdownRef}>
                  <button
                    className="flex items-center space-x-2 bg-gradient-to-r from-blue-50 to-purple-50 hover:from-blue-100 hover:to-purple-100 rounded-full px-3 py-2 transition-all duration-200 border border-blue-200 shadow-sm hover:shadow-md"
                    onClick={() => setDropdownOpen((open) => !open)}
                  >
                    <div className="w-7 h-7 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                      {user.name ? user.name.charAt(0).toUpperCase() : "U"}
                    </div>
                    <svg
                      className={`h-4 w-4 text-gray-600 transition-transform duration-200 ${
                        dropdownOpen ? "rotate-180" : ""
                      }`}
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                    </svg>
                  </button>

                  {dropdownOpen && (
                    <div className="absolute right-0 mt-2 w-52 bg-white rounded-xl shadow-xl border border-gray-100 z-50 overflow-hidden">
                      {/* User Info Header */}
                      <div className="px-4 py-3 bg-gradient-to-r from-blue-50 to-purple-50 border-b border-gray-100">
                        <div className="flex items-center space-x-3">
                          <div className="w-9 h-9 bg-gradient-to-r from-blue-500 to-purple-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                            {user.name ? user.name.charAt(0).toUpperCase() : "U"}
                          </div>
                          <div>
                            <p className="font-semibold text-gray-900 text-sm">{user.name || "User"}</p>
                            <p className="text-xs text-gray-500">{user.email || "user@example.com"}</p>
                          </div>
                        </div>
                      </div>

                      {/* Menu Items */}
                      <div className="py-1">
                        <button
                          className="w-full text-left px-4 py-2 hover:bg-blue-50 text-gray-700 font-medium transition-colors duration-150 flex items-center space-x-3 text-sm"
                          onClick={() => {
                            setDropdownOpen(false)
                            navigate("/profile")
                          }}
                        >
                          <svg className="h-4 w-4 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                            />
                          </svg>
                          <span>Profile Settings</span>
                        </button>
                        <button
                          className="w-full text-left px-4 py-2 hover:bg-red-50 text-red-600 font-medium transition-colors duration-150 flex items-center space-x-3 text-sm"
                          onClick={handleLogout}
                        >
                          <svg className="h-4 w-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1"
                            />
                          </svg>
                          <span>Sign Out</span>
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </header>

        {/* Main Content - Centered and Compact */}
        <div className="flex-1 flex items-center justify-center px-6 py-8">
          <div className="max-w-5xl w-full">
            {/* Welcome Section - Compact */}
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 mb-3">Your AI-Powered Cloud Architecture Hub</h2>
              <p className="text-lg text-gray-600 max-w-3xl mx-auto">
                Transform your ideas into optimized AWS architectures with intelligent recommendations
              </p>
            </div>

            {/* Quick Actions Section - Compact */}
            <div className="bg-white/70 backdrop-blur-sm rounded-2xl shadow-xl p-6 border border-white/50">
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 mb-1">Quick Actions</h3>
                  <p className="text-gray-600">Choose your next step to build amazing cloud solutions</p>
                </div>
                <div className="hidden md:flex items-center space-x-2 bg-gradient-to-r from-green-50 to-blue-50 px-3 py-2 rounded-full border border-green-200">
                  <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                  <span className="text-sm font-medium text-green-700">System Ready</span>
                </div>
              </div>

              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {quickActions.map((action, index) => (
                  <a
                    key={index}
                    href={action.link}
                    className={`group block p-6 rounded-xl bg-gradient-to-r ${action.color} ${action.hoverColor} text-white transform hover:scale-105 transition-all duration-300 shadow-lg hover:shadow-xl ${action.shadowColor} relative overflow-hidden`}
                  >
                    {/* Background Pattern - Subtle */}
                    <div className="absolute inset-0 opacity-10">
                      <div className="absolute -top-4 -right-4 w-16 h-16 bg-white rounded-full"></div>
                      <div className="absolute -bottom-4 -left-4 w-12 h-12 bg-white rounded-full"></div>
                    </div>

                    <div className="relative flex items-center space-x-4">
                      <div className="p-3 bg-white/20 rounded-lg group-hover:bg-white/30 transition-colors duration-300 backdrop-blur-sm">
                        {action.icon}
                      </div>
                      <div className="flex-1">
                        <h4 className="text-lg font-bold mb-1 group-hover:text-white transition-colors">
                          {action.title}
                        </h4>
                        <p className="text-white/90 text-sm leading-relaxed">{action.description}</p>
                      </div>
                      <div className="ml-auto transform group-hover:translate-x-1 transition-transform duration-300">
                        <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M13 7l5 5m0 0l-5 5m5-5H6"
                          />
                        </svg>
                      </div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  )
}

export default Dashboard
