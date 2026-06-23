import time
from retrieval import SemanticRetrievalStore

if __name__ == "__main__":
		
	store = SemanticRetrievalStore()

	for i in range(10000):
		store.add(f"This is test document number {i} about random topic {i % 10}")

	start = time.time()
	store.save("test_large.json")
	print(f"Save took: {time.time() - start:.4f}s")

	start = time.time()
	loaded = SemanticRetrievalStore.load("test_large.json")
	print(f"Load took: {time.time() - start:.4f}s")