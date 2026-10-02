"use client";

import { useState } from "react";

interface UserProfile {
  fullName: string;
  age: string;
  gender: string;
  state: string;
  district: string;
  category: string;
  course: string;
  yearOfStudy: string;
  annualFamilyIncome: string;
  disabilityStatus: string;
  searchQuery: string;
}

interface FieldComparison {
  field: string;
  status: string;
  reason: string;
  user_value: any;
  required_value: any;
  evidence: string | null;
}

interface EligibilityEvidence {
  matching_conditions: string[];
  mismatching_conditions: string[];
  unknown_requirements: string[];
  source_evidence: string[];
}

export default function UserProfileForm() {
  const [profile, setProfile] = useState<UserProfile>({
    fullName: "",
    age: "",
    gender: "",
    state: "",
    district: "",
    category: "",
    course: "",
    yearOfStudy: "",
    annualFamilyIncome: "",
    disabilityStatus: "No",
    searchQuery: "Find every scholarship I'm eligible for.",
  });

  const [liveSearchResults, setLiveSearchResults] = useState<any>(null);
  const [isLoadingLiveSearch, setIsLoadingLiveSearch] = useState(false);
  const [loadingProgress, setLoadingProgress] = useState(0);
  const [copiedScholarship, setCopiedScholarship] = useState<string | null>(null);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setProfile((prev) => ({ ...prev, [name]: value }));
  };

  const handleLiveSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setIsLoadingLiveSearch(true);
    setLoadingProgress(0);
    setLiveSearchResults(null);

    // Animate loading progress
    const progressInterval = setInterval(() => {
      setLoadingProgress((prev) => {
        if (prev >= 90) {
          clearInterval(progressInterval);
          return 90;
        }
        return prev + 10;
      });
    }, 200);
    
    try {
      const response = await fetch("http://13.62.229.119:8000/api/tavily/orchestrate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          query: `${profile.state} ${profile.category} ${profile.course} scholarship eligibility application`,
          profile: profile,
          max_results: 20,
        }),
      });

      if (!response.ok) {
        throw new Error("Failed to search official sources");
      }

      const data = await response.json();
      
      // Complete the progress
      clearInterval(progressInterval);
      setLoadingProgress(100);
      
      // Small delay before showing results
      setTimeout(() => {
        const transformedResults = {
          success: data.success,
          query: data.query,
          count: data.results?.length || 0,
          pipeline_summary: data.pipeline_summary || null,
          search_results: data.search_results || [],
          results: data.results?.filter((result: any) => {
          // Filter out results with garbage content
          const title = (result.scholarship_name || result.title || "").toLowerCase();
          const description = (result.benefits || "").toLowerCase();
          
          // Skip results with image references, OTR, URL paths, etc.
          const garbagePatterns = [
            "image 1:", "image 2:", "image 3:", "image 4:", "image 5:",
            "otr registration", "one time registration",
            "/en/", "/fresh/", "/public/", "/scheme",
            "0-", "-0", "may 17, 2022", "2022", "2023", "2024", "2025"
          ];
          
          const hasGarbage = garbagePatterns.some(pattern => 
            title.includes(pattern) || description.includes(pattern)
          );
          
          if (hasGarbage) return false;
          
          // Basic validation
          const hasValidTitle = title && title.length > 5 && title.length < 200;
          const hasValidDescription = description && description.length > 20;
          
          return hasValidTitle && hasValidDescription;
        }).map((result: any) => ({
            title: result.scholarship_name || result.title || "Untitled Scholarship",
            description: result.benefits || "Visit the official portal for detailed benefit information",
            deadline: result.deadline || "Visit portal for deadline",
            source: result.provider || result.source || "Official Portal",
            source_url: result.source_url || null,
            is_official: result.is_official !== false,
            eligibility_status: result.eligibility?.overall_status || null,
            field_comparisons: result.eligibility?.field_comparisons || [],
            evidence: result.eligibility?.evidence || null,
            pipeline_source: result.pipeline_source || "orchestrator",
            scraped_at: new Date().toISOString()
          })) || []
        };
        setLiveSearchResults(transformedResults);
        setLoadingProgress(0);
      }, 500);
      
    } catch (error) {
      console.error("Error:", error);
      clearInterval(progressInterval);
      setLoadingProgress(0);
      alert("Failed to search official sources. Please try again.");
    } finally {
      setIsLoadingLiveSearch(false);
    }
  };

  const copyScholarshipDetails = (scholarship: any) => {
    const details = `
Scholarship: ${scholarship.title}
Benefits: ${scholarship.description}
Deadline: ${scholarship.deadline || 'Not specified'}
Source: ${scholarship.source}

To apply:
1. Visit the official portal
2. Search for this scholarship by name
3. Submit your application with required documents
    `.trim();
    
    navigator.clipboard.writeText(details).then(() => {
      setCopiedScholarship(scholarship.title);
      setTimeout(() => setCopiedScholarship(null), 3000);
    });
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      {/* Header */}
      <div className="bg-white/80 backdrop-blur-lg border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-purple-600 rounded-xl flex items-center justify-center">
                <span className="text-white text-2xl font-bold">E</span>
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">EligibAI</h1>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form Section */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-xl border border-gray-100 overflow-hidden">
              <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
                <h2 className="text-xl font-semibold text-white">Your Profile</h2>
                <p className="text-blue-100 text-sm mt-1">Tell us about yourself</p>
              </div>
              
              <form onSubmit={handleLiveSearch} className="p-6 space-y-5">
                {/* Personal Information */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3 flex items-center">
                    <span className="w-8 h-8 bg-blue-100 rounded-lg flex items-center justify-center mr-2">
                      <span className="text-blue-600 text-sm">👤</span>
                    </span>
                    Personal Information
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                      <input
                        type="text"
                        name="fullName"
                        value={profile.fullName}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900 placeholder-gray-500"
                        placeholder="Enter your name"
                      />
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Age</label>
                        <input
                          type="number"
                          name="age"
                          value={profile.age}
                          onChange={handleInputChange}
                          required
                          min="15"
                          max="50"
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900 placeholder-gray-500"
                          placeholder="20"
                        />
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Gender</label>
                        <select
                          name="gender"
                          value={profile.gender}
                          onChange={handleInputChange}
                          required
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900"
                        >
                          <option value="">Select</option>
                          <option value="Male">Male</option>
                          <option value="Female">Female</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">State</label>
                        <select
                          name="state"
                          value={profile.state}
                          onChange={handleInputChange}
                          required
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900"
                        >
                          <option value="">Select State</option>
                          <option value="Andhra Pradesh">Andhra Pradesh</option>
                          <option value="Telangana">Telangana</option>
                          <option value="Karnataka">Karnataka</option>
                          <option value="Tamil Nadu">Tamil Nadu</option>
                          <option value="Maharashtra">Maharashtra</option>
                          <option value="Delhi">Delhi</option>
                          <option value="Uttar Pradesh">Uttar Pradesh</option>
                          <option value="West Bengal">West Bengal</option>
                          <option value="Gujarat">Gujarat</option>
                          <option value="Rajasthan">Rajasthan</option>
                          <option value="Kerala">Kerala</option>
                          <option value="Madhya Pradesh">Madhya Pradesh</option>
                          <option value="Punjab">Punjab</option>
                          <option value="Haryana">Haryana</option>
                          <option value="Bihar">Bihar</option>
                          <option value="Odisha">Odisha</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                        <select
                          name="category"
                          value={profile.category}
                          onChange={handleInputChange}
                          required
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900"
                        >
                          <option value="">Select</option>
                          <option value="General">General</option>
                          <option value="OBC">OBC</option>
                          <option value="SC">SC</option>
                          <option value="ST">ST</option>
                          <option value="EWS">EWS</option>
                        </select>
                      </div>
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">District (Optional)</label>
                      <input
                        type="text"
                        name="district"
                        value={profile.district}
                        onChange={handleInputChange}
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900 placeholder-gray-500"
                        placeholder="Your district"
                      />
                    </div>
                  </div>
                </div>

                {/* Education Information */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3 flex items-center">
                    <span className="w-8 h-8 bg-purple-100 rounded-lg flex items-center justify-center mr-2">
                      <span className="text-purple-600 text-sm">🎓</span>
                    </span>
                    Education
                  </h3>
                  <div className="space-y-3">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Course</label>
                        <select
                          name="course"
                          value={profile.course}
                          onChange={handleInputChange}
                          required
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900"
                        >
                          <option value="">Select</option>
                          <option value="B.Tech">B.Tech / B.E.</option>
                          <option value="Diploma">Diploma</option>
                          <option value="B.Sc">B.Sc</option>
                          <option value="B.Com">B.Com</option>
                          <option value="B.A">B.A</option>
                          <option value="M.Tech">M.Tech / M.E.</option>
                          <option value="M.Sc">M.Sc</option>
                          <option value="M.Com">M.Com</option>
                          <option value="MBA">MBA</option>
                          <option value="Other">Other</option>
                        </select>
                      </div>
                      
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">Year</label>
                        <select
                          name="yearOfStudy"
                          value={profile.yearOfStudy}
                          onChange={handleInputChange}
                          required
                          className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900"
                        >
                          <option value="">Select</option>
                          <option value="1st Year">1st Year</option>
                          <option value="2nd Year">2nd Year</option>
                          <option value="3rd Year">3rd Year</option>
                          <option value="4th Year">4th Year</option>
                          <option value="5th Year">5th Year</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Financial Information */}
                <div>
                  <h3 className="text-sm font-semibold text-gray-700 uppercase tracking-wider mb-3 flex items-center">
                    <span className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center mr-2">
                      <span className="text-green-600 text-sm">💰</span>
                    </span>
                    Financial
                  </h3>
                  <div className="space-y-3">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Annual Family Income (₹)</label>
                      <input
                        type="number"
                        name="annualFamilyIncome"
                        value={profile.annualFamilyIncome}
                        onChange={handleInputChange}
                        required
                        min="0"
                        step="1000"
                        placeholder="e.g., 300000"
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900 placeholder-gray-500"
                      />
                    </div>
                    
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">Disability Status</label>
                      <select
                        name="disabilityStatus"
                        value={profile.disabilityStatus}
                        onChange={handleInputChange}
                        required
                        className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900"
                      >
                        <option value="No">No</option>
                        <option value="Yes">Yes</option>
                      </select>
                    </div>
                  </div>
                </div>

                {/* Search Query */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">What are you looking for?</label>
                  <textarea
                    name="searchQuery"
                    value={profile.searchQuery}
                    onChange={handleInputChange}
                    rows={3}
                    className="w-full px-4 py-2.5 border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all bg-white text-gray-900 placeholder-gray-500 resize-none"
                    placeholder="Describe what kind of scholarships you're looking for..."
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoadingLiveSearch}
                  className="w-full bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white font-semibold py-3.5 px-4 rounded-xl transition-all transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                >
                  {isLoadingLiveSearch ? (
                    <span className="flex flex-col items-center justify-center">
                      <div className="w-full bg-gray-200 rounded-full h-2 mb-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-200"
                          style={{ width: `${loadingProgress}%` }}
                        ></div>
                      </div>
                      <span className="text-sm">Searching... {loadingProgress}%</span>
                    </span>
                  ) : (
                    <span className="flex items-center justify-center">
                      <span className="mr-2">🔍</span>
                      Search Scholarships
                    </span>
                  )}
                </button>
              </form>
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            {liveSearchResults ? (
              <div className="space-y-6">
                {/* Results Header */}
                <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">Search Results</h2>
                      <p className="text-gray-500 mt-1">Scholarships from government portals and reliable sources</p>
                    </div>
                  </div>

                  <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
                    <p className="text-sm text-blue-800 mb-2">
                      <span className="font-medium">ℹ️ Note:</span> These results are from real-time web search. Click "Apply on Portal" to visit the official source and check eligibility requirements, deadlines, and application details. Always verify information on the official portal before applying.
                    </p>
                    <p className="text-sm text-orange-800">
                      <span className="font-medium">⚠️ Important:</span> Some government portals may be temporarily unavailable, slow, or under maintenance. If a link doesn't work, try again later or visit the portal directly during office hours.
                    </p>
                  </div>
                  
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4">
                      <p className="text-sm text-blue-600 font-medium">Scholarships Found</p>
                      <p className="text-2xl font-bold text-blue-900">{liveSearchResults.count}</p>
                    </div>
                    <div className="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4">
                      <p className="text-sm text-green-600 font-medium">Data Freshness</p>
                      <p className="text-2xl font-bold text-green-900">Real-time</p>
                    </div>
                  </div>
                </div>

                {/* Scholarships List */}
                {liveSearchResults.results?.length > 0 ? (
                  <div className="space-y-4">
                    {liveSearchResults.results.map((result: any, index: number) => (
                      <div
                        key={index}
                        className="bg-white rounded-2xl shadow-lg border border-gray-100 overflow-hidden hover:shadow-xl transition-shadow"
                      >
                        <div className="p-6">
                          <div className="flex items-start justify-between mb-4">
                            <div className="flex-1">
                              <div className="flex items-center flex-wrap gap-2 mb-3">
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                  result.is_official === false
                                    ? "bg-blue-100 text-blue-800"
                                    : "bg-green-100 text-green-800"
                                }`}>
                                  {result.is_official === false
                                    ? "🔵 " + (result.source || "Aggregator")
                                    : "🟢 " + (result.source || "Government Portal")}
                                </span>
                                <span className={`px-3 py-1 rounded-full text-xs font-medium ${
                                  result.extraction_method === "gemini"
                                    ? "bg-purple-100 text-purple-800"
                                    : "bg-yellow-100 text-yellow-800"
                                }`}>
                                  {result.extraction_method === "gemini"
                                    ? "✨ AI Extracted"
                                    : "⚠️ Mock Extracted"}
                                </span>
                              </div>
                              <h3 className="text-xl font-bold text-gray-900 mb-2">
                                {result.title || "Untitled Scholarship"}
                              </h3>
                              {result.description && result.description !== "Visit the official portal for detailed benefit information" && (
                                <p className="text-gray-600 text-sm leading-relaxed mb-3">
                                  {result.description}
                                </p>
                              )}
                              
                              {result.source && result.source.includes("Fallback") && (
                                <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-3">
                                  <p className="text-xs text-blue-800">
                                    <span className="font-medium">💡 Tip:</span> Navigate to the official portal and search for this scholarship by name to apply.
                                  </p>
                                </div>
                              )}
                              
                            </div>
                          </div>

                          <div className="flex items-center justify-end pt-4 border-t border-gray-100">
                            <div className="flex items-center space-x-2">
                              {result.source_url && (
                                <a
                                  href={result.source_url}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="inline-flex items-center px-4 py-2 bg-gradient-to-r from-blue-600 to-purple-600 text-white rounded-lg text-sm font-medium hover:from-blue-700 hover:to-purple-700 transition-all"
                                >
                                  Apply on Portal
                                  <svg className="ml-2 w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                                  </svg>
                                </a>
                              )}
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-12 text-center">
                    <div className="w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mx-auto mb-4">
                      <span className="text-3xl">🔍</span>
                    </div>
                    <h3 className="text-xl font-semibold text-gray-900 mb-2">No Scholarships Found</h3>
                    <p className="text-gray-600 mb-4">
                      We couldn't find scholarships matching your criteria. Try adjusting your search query or profile information.
                    </p>
                    <div className="flex items-center justify-center space-x-2 text-sm text-gray-500">
                      <span>Tips:</span>
                      <span>• Try broader search terms</span>
                      <span>• Check different categories</span>
                      <span>• Verify your state selection</span>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-12 text-center">
                <div className="w-20 h-20 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full flex items-center justify-center mx-auto mb-6">
                  <span className="text-4xl">🎓</span>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-3">Find Your Perfect Scholarship</h2>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  Fill out your profile and we'll search government portals and reliable sources in real-time to find scholarships that match your eligibility. Note: Some government portals may be temporarily unavailable.
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}