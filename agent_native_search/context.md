# Educational Resource Search - Accumulated Knowledge

This file accumulates knowledge about what works for educational resource search across different countries, grades, and subjects.

**Last Updated:** 2026-01-12

---

## System Status

### Available Search Methods
- **Rule-Based Search**: ✅ Operational
  - Fast, reliable, returns platform recommendations
  - Best for: Well-defined queries (country + grade + subject)
  - Limitations: Returns platform homepages, not specific resources

- **AI Search**: ❌ Under Development
  - Returns 501 Not Implemented
  - Planned for: 2026 Q2

---

## Country-Specific Knowledge

### Indonesia (ID)

#### Configuration Status
- **Country Code**: ID
- **Language**: Indonesian (Bahasa Indonesia)
- **Curriculum**: Kurikulum Merdeka
- **Supported Grades**: 1, 2, 3, 4, 5, 6 (Elementary/SD)

#### What Works

**Grade 1 Math:**
- ✅ **Best Query**: "Matematika SD Kelas 1 Kurikulum Merdeka"
- ✅ **Top Score**: 9.5/10
- ✅ **Platforms**: Ruangguru, YouTube, Zenius, Khan Academy
- ✅ **Language Tip**: Use "Matematika" not "Math"

**Grade 1 Science:**
- ⚠️ **Status**: Not fully configured yet
- ✅ **Workaround**: Try Grade 1 Math (some science content included)
- ❌ **Query**: "IPA SD Kelas 1" returns poor results

#### Trusted Domains
- ruangguru.com: 10.0 (Indonesian platform, highly relevant)
- zenius.net: 9.5 (Indonesian education)
- youtube.com: 8.0 (General platform, but has educational content)
- khanacademy.org: 8.0 (International, supports Indonesian)
- kemdikbud.go.id: 9.0 (Official Indonesian education portal)

#### Search Tips
- Use Indonesian terms: "Matematika" instead of "Math"
- Include curriculum: "Kurikulum Merdeka"
- Specify grade level: "SD Kelas 1" for Grade 1
- For video content: Add "video" or "tutorial" to query

---

### Saudi Arabia (SA)

#### Configuration Status
- **Country Code**: SA
- **Language**: Arabic
- **Curriculum**: Saudi National Curriculum
- **Supported Grades**: Not yet configured

#### What Works
- ⚠️ **Status**: Limited configuration
- ✅ **Fallback**: DEFAULT config may work

---

### China (CN)

#### Configuration Status
- **Country Code**: CN
- **Language**: Chinese (Simplified)
- **Curriculum**: Not specified
- **Supported Grades**: Not yet configured

---

### United States (US)

#### Configuration Status
- **Country Code**: US
- **Language**: English
- **Curriculum**: Common Core
- **Supported Grades**: Not yet configured

---

## Search Patterns

### Successful Patterns

| Country | Grade | Subject | Query Template | Top Score | Notes |
|---------|-------|---------|----------------|-----------|-------|
| ID | 1 | math | {subject} SD Kelas {grade} Kurikulum Merdeka | 9.5 | Use Indonesian terms |
| ID | 1 | math | Matematika Sekolah Dasar Kelas 1 | 9.0 | Formal language |
| ID | 3 | math | Matematika SD Kelas 3 | 8.5 | Simple works well |

### Failed Patterns

| Country | Grade | Subject | Query Template | Score | Why It Failed |
|---------|-------|---------|----------------|-------|---------------|
| ID | 1 | science | Science Grade 1 | 2.0 | English term, not configured |
| ID | 2 | science | IPA SD Kelas 2 | 0.0 | Grade 2 not configured |
| ID | 1 | math | Calculus Grade 1 | 1.5 | Age-inappropriate |

---

## Common Issues and Solutions

### Issue: Poor Quality Results (Score < 5.0)

**Possible Causes:**
1. Wrong language (using English instead of local language)
2. Grade not configured
3. Subject not configured
4. Age-inappropriate query (e.g., calculus for grade 1)

**Solutions:**
1. Try local language terms
2. Check configuration first with `get_config`
3. Use broader query
4. Suggest alternative grade/subject

### Issue: Empty Results

**Possible Causes:**
1. Country not configured
2. No DEFAULT config available
3. Very specific query with no matches

**Solutions:**
1. Check `list_supported_countries` first
2. Try a different country
3. Use broader query terms
4. Explain limitation to user

### Issue: Returns Platform Homepages Only

**This is expected behavior** for the current system:
- MockSearchEngine returns platform recommendations
- Not specific resource URLs
- Agent should guide users to search within platforms

**Future Improvement:**
- Integrate real search engine (search_engine_v2 or external API)
- Return specific resource URLs
- Validate URLs before returning

---

## Platform Knowledge

### Ruangguru (Indonesia)
- **URL**: https://www.ruangguru.com/
- **Focus**: K-12 education, all subjects
- **Language**: Indonesian
- **Quality**: High, trusted domain (10.0/10)
- **Best For**: Structured courses, practice exercises
- **Usage Hint**: Search within the platform for specific topics

### Zenius (Indonesia)
- **URL**: https://www.zenius.net/
- **Focus**: High school and exam prep
- **Language**: Indonesian
- **Quality**: High (9.5/10)
- **Best For**: Deep understanding, concept videos
- **Usage Hint**: Some free content, some paid

### YouTube
- **URL**: https://www.youtube.com/
- **Focus**: Video content
- **Language**: All languages
- **Quality**: Variable (8.0/10)
- **Best For**: Visual learning, tutorials
- **Usage Hint**: Search with specific keywords and language

### Khan Academy
- **URL**: https://www.khanacademy.org/
- **Focus**: International curriculum
- **Language**: Multiple (including Indonesian)
- **Quality**: High (8.0/10)
- **Best For**: Structured learning, practice
- **Usage Hint**: Change language settings to Indonesian

### Indonesian Ministry of Education (Kemdikbud)
- **URL**: https://www.kemdikbud.go.id/
- **Focus**: Official resources, curriculum
- **Language**: Indonesian
- **Quality**: Authoritative (9.0/10)
- **Best For**: Official curriculum materials, textbooks
- **Usage Hint**: Look for "Kurikulum Merdeka" resources

---

## Agent Behavior Insights

### What Users Appreciate
1. Transparency about system limitations
2. Clear explanation of search strategy
3. Helpful alternatives when search fails
4. Learning from past searches
5. Presenting results in organized way

### What Users Find Frustrating
1. Pretending the system works when it doesn't
2. Returning fake/dead URLs (fixed in current version)
3. Not explaining why results are poor
4. Giving up after first failure
5. Hiding AI search limitations

### Effective Agent Patterns

**Pattern 1: Verify Before Search**
```
1. Check if country is configured
2. Check if grade is supported
3. Check if subject is available
4. Tell user what to expect
5. Then execute search
```

**Pattern 2: Iterate on Poor Results**
```
1. First search with best guess
2. Check score and relevance
3. If poor (< 5.0), try variations:
   - Different language (local vs English)
   - Different terms (synonyms)
   - Broader query
4. Present best results
```

**Pattern 3: Honest Communication**
```
⚠️ Current Limitations:
- Rule-based search only
- Returns platform recommendations
- Grade 2 Science not configured
- AI search under development

✅ What I Can Do:
- Find math resources for Grade 1, 3-6
- Recommend trusted platforms
- Guide you to specific resources within platforms
```

---

## Future Improvements

### High Priority
1. **Integrate Real Search Engine**
   - Replace MockSearchEngine with search_engine_v2
   - Return specific resource URLs
   - Validate all URLs before returning

2. **Add More Country Configurations**
   - Complete Indonesia (all grades, all subjects)
   - Add Saudi Arabia configuration
   - Add China configuration
   - Add United States configuration

3. **Implement AI Search**
   - Currently returns 501
   - Could use LLM for semantic understanding
   - Better handling of ambiguous queries

### Medium Priority
4. **Add URL Health Check**
   - Periodically verify platform URLs
   - Alert if platforms become unavailable
   - Update trusted domain scores

5. **Improve Result Specificity**
   - Return specific resource URLs
   - Not just platform homepages
   - Direct links to videos/textbooks/exercises

### Low Priority
6. **Add User Feedback Loop**
   - Let users rate result quality
   - Learn from successful searches
   - Adapt search strategies based on feedback

---

## Metadata

**Knowledge Version**: 1.0
**Last Agent Training**: 2026-01-12
**Searches Analyzed**: 5
**Successful Patterns**: 3
**Failed Patterns**: 2
**Countries Configured**: 1 (Indonesia partial)

**Next Review**: After 100 searches or 1 week, whichever comes first
