// Simple test script to verify the API endpoint
const testApi = async () => {
  const baseUrl = 'http://localhost:3000';
  
  // Test data
  const testData = {
    job: 'scrap',
    params: {
      source: 'syosetu',
      workId: 'n2596la',
      episodes: 1,
    },
  };

  try {
    console.log('Testing API endpoint...');
    console.log('Request data:', JSON.stringify(testData, null, 2));
    
    const response = await fetch(`${baseUrl}/api/execute`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(testData)
    });

    const result = await response.json();
    
    console.log('Response status:', response.status);
    console.log('Response data:', JSON.stringify(result, null, 2));
    
    if (response.ok) {
      console.log('✅ API test successful!');
    } else {
      console.log('❌ API test failed!');
    }
    
  } catch (error) {
    console.error('❌ Test failed with error:', error.message);
  }
};

// Run the test
testApi();
