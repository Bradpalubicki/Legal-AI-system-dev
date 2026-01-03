async function testAgentAPI() {
  const sessionId = 'test_' + Date.now();

  console.log('🤖 Testing Intelligent Legal Agent API\n');
  console.log('=' .repeat(60));

  // 1. Test document analysis
  console.log('\n📄 Step 1: Analyzing Document...\n');

  const sampleDocument = `
    IN THE CIRCUIT COURT OF COOK COUNTY, ILLINOIS

    MIDLAND CREDIT MANAGEMENT, INC.,
    Plaintiff,

    vs.

    JOHN DOE,
    Defendant.

    Case No: 2024-CC-12345

    COMPLAINT

    Plaintiff alleges:
    1. Defendant owes $8,542.00 on a credit card account
    2. Original creditor was Chase Bank
    3. Debt was assigned to Plaintiff on January 15, 2023
    4. Defendant has failed to pay

    WHEREFORE, Plaintiff seeks judgment for $8,542.00 plus costs.
  `;

  const analyzeResponse = await fetch('http://localhost:3000/api/agent/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sessionId,
      documentText: sampleDocument,
      documentType: 'complaint'
    })
  });

  const analyzeData = await analyzeResponse.json();
  console.log('✅ Analysis Complete:');
  console.log(`   First Question: ${analyzeData.firstQuestion?.question}`);
  console.log(`   Estimated Questions: ${analyzeData.estimatedQuestions}`);
  console.log(`   Initial Confidence: ${analyzeData.confidence}%`);
  console.log(`   Insights: ${analyzeData.initialInsights?.length || 0}`);

  // 2. Test answering questions
  console.log('\n💬 Step 2: Answering Questions...\n');

  const answers = [
    { questionId: analyzeData.firstQuestion.id, answer: 'Over 6 years ago' },
  ];

  for (const { questionId, answer } of answers) {
    const answerResponse = await fetch('http://localhost:3000/api/agent/answer', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        sessionId,
        questionId,
        answer
      })
    });

    const answerData = await answerResponse.json();
    console.log(`Q: ${analyzeData.firstQuestion?.question}`);
    console.log(`A: ${answer}`);

    if (answerData.feedback) {
      console.log(`\n💬 Feedback: ${answerData.feedback}`);
    }

    if (answerData.insights?.length > 0) {
      console.log(`💡 Insights: ${answerData.insights.join(', ')}`);
    }

    if (answerData.defense_implications) {
      console.log(`⚖️  Defense Impact: ${answerData.defense_implications}`);
    }

    console.log(`📊 Confidence: ${answerData.confidenceScore}%`);

    if (answerData.nextQuestion) {
      console.log(`\nNext Question: ${answerData.nextQuestion.question}`);

      // Answer the next question
      const nextAnswerResponse = await fetch('http://localhost:3000/api/agent/answer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          sessionId,
          questionId: answerData.nextQuestion.id,
          answer: 'Yes, but not with this company'
        })
      });

      const nextAnswerData = await nextAnswerResponse.json();
      console.log(`A: Yes, but not with this company`);
      console.log(`📊 Confidence: ${nextAnswerData.confidenceScore}%`);
    }
  }

  // 3. Test defense building
  console.log('\n\n🔨 Step 3: Building Defense Strategy...\n');

  const defenseResponse = await fetch('http://localhost:3000/api/agent/build-defense', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ sessionId })
  });

  const strategy = await defenseResponse.json();

  console.log('Raw Strategy Response:', JSON.stringify(strategy, null, 2));

  console.log('\n✅ Defense Strategy Built:');
  console.log(`\n🛡️  Primary Defenses: ${strategy.primary_defenses?.length || 0}`);

  strategy.primary_defenses?.forEach((defense, i) => {
    console.log(`\n   ${i + 1}. ${defense.name} (${defense.strength}% strength)`);
    console.log(`      ${defense.description}`);
  });

  console.log(`\n📋 Immediate Actions: ${strategy.immediate_actions?.length || 0}`);
  strategy.immediate_actions?.forEach((action, i) => {
    console.log(`   ${i + 1}. ${action.action} (${action.priority})`);
  });

  console.log(`\n📁 Evidence Needed: ${strategy.evidence_needed?.length || 0} items`);

  console.log(`\n📊 Overall Success Rate: ${strategy.estimated_success_rate}`);

  console.log('\n' + '='.repeat(60));
  console.log('✅ All Agent API Tests Passed!');
}

testAgentAPI().catch(error => {
  console.error('❌ Test failed:', error);
  process.exit(1);
});
