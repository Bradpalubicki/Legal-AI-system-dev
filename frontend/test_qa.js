async function testQA() {
  const questions = [
    'What is my deadline?',
    'How much are they claiming?',
    'What type of case is this?',
    'What should I do first?',
    'Should I get a lawyer?',
    'What happens if I ignore this?',
    'Tell me about defenses',  // Should redirect
    'What are my defense options?'  // Should redirect
  ];

  console.log('Testing Q&A responses...\n');
  console.log('='.repeat(60));

  for (const q of questions) {
    try {
      const response = await fetch('http://localhost:3000/api/qa-only', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: q })
      });

      if (!response.ok) {
        console.error(`❌ HTTP Error ${response.status} for: ${q}`);
        console.log('---\n');
        continue;
      }

      const data = await response.json();

      console.log(`Q: ${q}`);
      console.log(`A: ${data.response}`);

      // Check for forbidden defense content
      const forbiddenPhrases = [
        'DEFENSE OPTIONS',
        'TO BUILD YOUR DEFENSE',
        'Statute of Limitations',
        'Lack of Evidence',
        'Procedural Errors',
        'Your defenses are',
        'BUILD A DEFENSE',
        'affirmative defense'
      ];

      let hasForbidden = false;
      for (const phrase of forbiddenPhrases) {
        if (data.response.includes(phrase)) {
          console.error(`❌ ERROR: Q&A is outputting defense content: "${phrase}"`);
          hasForbidden = true;
          break;
        }
      }

      if (!hasForbidden) {
        console.log('✅ Correct: Answer without defense content');
      }

      // Check response type
      if (data.type !== 'answer') {
        console.error(`❌ ERROR: Wrong type. Expected 'answer', got '${data.type}'`);
      } else {
        console.log('✅ Correct: Type is "answer"');
      }

      console.log('---\n');

    } catch (error) {
      console.error(`❌ Exception for "${q}":`, error.message);
      console.log('---\n');
    }
  }

  console.log('='.repeat(60));
  console.log('Test complete!');
}

// Run the test
testQA().catch(error => {
  console.error('Test failed:', error);
  process.exit(1);
});
