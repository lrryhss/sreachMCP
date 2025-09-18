# Multi-Step Prompting for Detailed Analysis with Gemma 3

## Overview
Transform the detailed analysis generation from a single complex prompt to a multi-step approach that leverages Gemma 3's capabilities and large context window.

## Current Issues
- Single complex prompt overwhelms the model
- Limited context (8192 tokens) restricts data passing
- Model fails to generate structured detailed_analysis
- Falls back to theme-based structure

## Solution: Multi-Step Prompting with Increased Context

### Phase 1: Configuration Updates
1. **Increase Context Window**
   - Update `context_length: 8192` to `context_length: 32768`
   - Update `num_predict: 2048` to `num_predict: 4096`
   - Adjust max_tokens in generate calls to 4096

### Phase 2: New Multi-Step Methods in ollama_client.py

#### Method 1: generate_analysis_outline()
```python
async def generate_analysis_outline(self, summaries: List[Dict], query: str) -> List[str]:
    """Generate outline of main sections for detailed analysis"""
    # Returns: List of 5-8 section titles
```

#### Method 2: generate_section_content()
```python
async def generate_section_content(
    self,
    section_title: str,
    summaries: List[Dict],
    query: str
) -> Dict[str, Any]:
    """Generate detailed content for a specific section"""
    # Returns: Content with 2-3 paragraphs
```

#### Method 3: extract_quotes_and_stats()
```python
async def extract_quotes_and_stats(
    self,
    section_content: str,
    sources: List[Dict]
) -> Dict[str, Any]:
    """Extract quotes and statistics from section content"""
    # Returns: Structured quotes and statistics
```

#### Method 4: generate_subsections()
```python
async def generate_subsections(
    self,
    section_title: str,
    section_content: str
) -> List[Dict[str, str]]:
    """Generate subsections if needed"""
    # Returns: 1-2 subsections with content
```

#### Method 5: generate_detailed_analysis_multistep()
```python
async def generate_detailed_analysis_multistep(
    self,
    summaries: List[Dict],
    query: str
) -> Dict[str, Any]:
    """Orchestrate multi-step detailed analysis generation"""
    # Main method that calls all steps and assembles final structure
```

### Phase 3: Integration in orchestrator.py
- Keep existing synthesize_research for basic synthesis
- Add call to generate_detailed_analysis_multistep after basic synthesis
- Update progress tracking between steps

### Progress Tracking
- 70%: Starting synthesis
- 75%: Generating outline
- 80%: Writing section content
- 85%: Extracting quotes/statistics
- 90%: Adding subsections
- 95%: Finalizing structure

## Implementation Steps

### Step 1: Update Configuration
- File: `config/default.yaml`
- Changes:
  - context_length: 32768
  - num_predict: 4096

### Step 2: Create Multi-Step Methods
- File: `src/clients/ollama_client.py`
- Add all new methods listed above
- Keep existing synthesize_research as is

### Step 3: Update Orchestrator
- File: `src/agent/orchestrator.py`
- Call new multi-step method after basic synthesis
- Add progress updates between steps

### Step 4: Test and Refine
- Run research query
- Verify detailed_analysis structure is generated
- Check frontend displays enhanced content

## Benefits
1. **Better Quality**: Each prompt is focused and manageable
2. **More Reliable**: Less chance of model confusion
3. **Flexible**: Can adjust each step independently
4. **Debuggable**: Can see exactly where issues occur
5. **Token Efficient**: Better use of Gemma 3's 128K context
6. **Richer Content**: Can generate longer, more detailed sections

## Expected Output Structure
```json
{
  "detailed_analysis": {
    "sections": [
      {
        "title": "Section Title",
        "content": "2-3 paragraphs of detailed content",
        "quotes": [
          {
            "text": "Direct quote",
            "source_id": 1,
            "author": "Author Name"
          }
        ],
        "statistics": {
          "key_metric": "value",
          "percentage": "85%"
        },
        "sources": [1, 2, 3],
        "subsections": [
          {
            "subtitle": "Subsection Title",
            "content": "1-2 paragraphs"
          }
        ]
      }
    ]
  }
}
```

## Files to Modify
1. `/config/default.yaml` - Context and token limits
2. `/src/clients/ollama_client.py` - New multi-step methods
3. `/src/agent/orchestrator.py` - Integration point

## Testing Plan
1. Update configuration
2. Implement multi-step methods
3. Test with sample research query
4. Verify detailed_analysis is properly generated
5. Confirm frontend displays enhanced content correctly