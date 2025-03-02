from sentence_transformers import SentenceTransformer
import faiss
import numpy as np

a = SentenceTransformer('all-MiniLM-L6-v2')

class QuoteReplacer:
    def __init__(self, body: str):
        """
        Initialize the QuoteReplacer with the body of text containing quotes.
        """
        self.body = body
        self.quotes = self._split_body_into_quotes()
        self.model = a
        self.quote_embeddings = self._compute_embeddings(self.quotes)
        self.index = self._build_faiss_index(self.quote_embeddings)

    def _split_body_into_quotes(self):
        """
        Split the body of text into individual quotes.
        This is a simple implementation and may need adjustments based on the actual format of the text.
        """
        return [quote.strip() for quote in self.body.split('\n') if quote.strip()]

    def _compute_embeddings(self, texts):
        """
        Compute embeddings for a list of texts using the SentenceTransformer model.
        """
        return np.array(self.model.encode(texts)).astype('float32')

    def _build_faiss_index(self, embeddings):
        """
        Build a FAISS index for the given embeddings.
        """
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatL2(dimension)
        index.add(embeddings)
        return index

    def find_exact_quote(self, approximate_quote: str):
        """
        Find and return the exact quote from the body that is most similar to the approximate quote.
        """
        query_embedding = np.array(self.model.encode([approximate_quote])).astype('float32')
        distances, indices = self.index.search(query_embedding, 1)
        best_match_index = indices[0][0]
        return self.quotes[best_match_index]