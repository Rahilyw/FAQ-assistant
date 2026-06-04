-- ============================================================
-- RAG Pipeline – FAQ Assistant
-- Exercise 3: Retrieval-Augmented Generation with Azure SQL
-- ============================================================
-- Part 1: Retrieve FAQ data and build the grounding context
-- Part 2: Send the grounded prompt to GPT-4o
-- ============================================================

DROP TABLE IF EXISTS #searchResults;

DECLARE @user_question NVARCHAR(1000) = N'My product arrived damaged';
DECLARE @context NVARCHAR(MAX);
DECLARE @prompt NVARCHAR(MAX);

CREATE TABLE #searchResults (
  faq_id    INT,
  category  NVARCHAR(200),
  question  NVARCHAR(MAX),
  answer    NVARCHAR(MAX)
);

INSERT INTO #searchResults (faq_id, category, question, answer)
EXEC dbo.SearchFAQ @user_question = @user_question;

SELECT @context =
(
  SELECT STRING_AGG(
      CONCAT(
        'Question: ', question, CHAR(10),
        'Answer: ', answer
      ),
      CHAR(10) + CHAR(10)
  )
  FROM #searchResults
);

SET @prompt =
N'Use ONLY the context below to answer the question.

Context:
' + ISNULL(@context, N'No relevant FAQ context found.') + N'

Question:
' + @user_question + N'

If the answer is not in the context, say you do not know.';

DROP TABLE #searchResults;

-- ============================================================
-- Part 2: Send grounded prompt to GPT-4o via Azure OpenAI
-- ============================================================

DECLARE @payload  NVARCHAR(MAX);
DECLARE @response NVARCHAR(MAX);
DECLARE @headers  NVARCHAR(MAX) = N'{"api-key": "<your-azure-openai-api-key>"}';

SET @payload = N'{' +
  N'"messages":[' +
      N'{"role":"system","content":"You are a helpful assistant that answers using ONLY the provided context."},' +
      N'{"role":"user","content":' + N'"' + STRING_ESCAPE(@prompt, 'json') + N'"' + N'}' +
  N'],' +
  N'"temperature":0' +
N'}';

EXEC sp_invoke_external_rest_endpoint
  @method  = 'POST',
  @url     = N'https://<your-openai-resource>.cognitiveservices.azure.com/openai/deployments/GPT-4o/chat/completions?api-version=2025-01-01-preview',
  @headers = @headers,
  -- For production, prefer: @credential = N'your_db_scoped_credential'
  @payload  = @payload,
  @response = @response OUTPUT;

SELECT
  @response AS raw_response,
  COALESCE(
    JSON_VALUE(@response, '$.result.choices[0].message.content'),
    JSON_VALUE(@response, '$.choices[0].message.content'),
    JSON_VALUE(@response, '$.output[0].content[0].text'),
    @response
  ) AS ai_answer;
