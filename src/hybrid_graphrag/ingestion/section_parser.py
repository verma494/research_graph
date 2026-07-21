import re
from typing import List, Optional
from ..schemas import ExtractedDocument, SectionBlock
import tiktoken

class SectionParser:
    def __init__(self):
        # We will use tiktoken to count tokens immediately when creating the section block
        self.encoder = tiktoken.get_encoding("cl100k_base")
        
        # Regex heuristics for detecting major scholarly headings
        self.heading_pattern = re.compile(
            r'^\s*([0-9\.]+)?\s*(Abstract|Introduction|Background|Related Work|Methodology|Methods|Materials and Methods|Results|Discussion|Conclusion|Conclusions|References)\s*$',
            re.IGNORECASE | re.MULTILINE
        )

    def parse_sections(self, document: ExtractedDocument) -> List[SectionBlock]:
        if not document.full_text:
            return []
            
        matches = list(self.heading_pattern.finditer(document.full_text))
        
        if not matches:
            # Fallback: no sections found, treat the whole document as one section
            return [self._create_block("Full Text", document.full_text)]
            
        blocks = []
        last_idx = 0
        last_name = "Header"
        
        if matches[0].start() > 0:
            blocks.append(self._create_block(last_name, document.full_text[0:matches[0].start()]))
            
        for i, match in enumerate(matches):
            name = match.group(2).strip().title()
            start_idx = match.end()
            end_idx = matches[i+1].start() if i + 1 < len(matches) else len(document.full_text)
            
            text = document.full_text[start_idx:end_idx].strip()
            if text:
                blocks.append(self._create_block(name, text))
                
        return blocks

    def _create_block(self, name: str, text: str) -> SectionBlock:
        token_count = len(self.encoder.encode(text, disallowed_special=()))
        return SectionBlock(name=name, text=text, token_count=token_count)
