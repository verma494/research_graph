import tiktoken
from typing import List
from ..schemas import SectionBlock, ChunkRecord, Paper
from ..utils.ids import generate_deterministic_id

class TokenChunker:
    def __init__(self, max_tokens: int = 800, min_standalone: int = 500, overlap: int = 100):
        self.max_tokens = max_tokens
        self.min_standalone = min_standalone
        self.overlap = overlap
        self.encoder = tiktoken.get_encoding("cl100k_base")

    def chunk_paper(self, paper: Paper, sections: List[SectionBlock]) -> List[ChunkRecord]:
        chunks = []
        chunk_number = 1
        
        for section in sections:
            tokens = self.encoder.encode(section.text, disallowed_special=())
            
            if len(tokens) <= self.max_tokens:
                
                text = self.encoder.decode(tokens)
                chunk_id = generate_deterministic_id(paper.id, section.name, chunk_number)
                chunks.append(
                    ChunkRecord(
                        chunk_id=chunk_id,
                        paper_id=paper.id,
                        section=section.name,
                        text=text,
                        chunk_number=chunk_number,
                        token_count=len(tokens)
                    )
                )
                chunk_number += 1
            else:
                # Needs splitting
                for start_idx in range(0, len(tokens), self.max_tokens - self.overlap):
                    end_idx = start_idx + self.max_tokens
                    chunk_tokens = tokens[start_idx:end_idx]
                    text = self.encoder.decode(chunk_tokens)
                    chunk_id = generate_deterministic_id(paper.id, section.name, chunk_number)
                    chunks.append(
                        ChunkRecord(
                            chunk_id=chunk_id,
                            paper_id=paper.id,
                            section=section.name,
                            text=text,
                            chunk_number=chunk_number,
                            token_count=len(chunk_tokens)
                        )
                    )
                    chunk_number += 1
                    
        if chunks:
            paper.processing_status = "chunked"
        
        return chunks
