# CLAUDE.md - AI Assistant Guide for weatherdataexplained.com

## Project Overview

**Project Name:** Weather Data Explained
**Repository:** marek-rodny/weatherdataexplained.com
**License:** GNU General Public License v3.0
**Purpose:** A website/web application for explaining weather data in an accessible and educational manner

### Current Status
This is a newly initialized repository. The project structure and technology stack are yet to be established.

---

## Repository Structure

### Current Structure
```
weatherdataexplained.com/
├── .git/              # Git version control
├── LICENSE            # GPL v3.0 license
├── README.md          # Project overview
└── CLAUDE.md          # This file - AI assistant guide
```

### Expected Future Structure
As the project develops, expect to see:
```
weatherdataexplained.com/
├── src/               # Source code
│   ├── components/    # Reusable UI components
│   ├── pages/         # Page components
│   ├── styles/        # CSS/styling files
│   ├── utils/         # Utility functions
│   └── api/           # API integrations (weather data sources)
├── public/            # Static assets
├── tests/             # Test files
├── docs/              # Documentation
├── .github/           # GitHub workflows and templates
├── package.json       # Dependencies (if Node.js-based)
└── [config files]     # Build and tooling configuration
```

---

## Development Workflows

### Branch Strategy

**Main Branch:** `main` (or `master`)
- Protected branch
- Contains production-ready code
- All changes must go through pull requests

**Feature Branches:**
- Named with prefix: `claude/claude-md-{session-id}`
- Created for each development task
- Should be short-lived and focused on specific features

### Git Commit Guidelines

**Commit Message Format:**
```
<type>: <subject>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks, dependencies

**Examples:**
```
feat: add temperature conversion utility
fix: correct humidity calculation in WeatherCard component
docs: update API integration guide
```

### Pull Request Process

1. **Create feature branch** from main
2. **Develop and commit** changes with clear messages
3. **Push to origin** with `git push -u origin <branch-name>`
4. **Create pull request** with:
   - Clear title summarizing the changes
   - Description with:
     - Summary of changes (bullet points)
     - Test plan (how to verify the changes)
     - Screenshots (if UI changes)
5. **Address review feedback** if applicable
6. **Merge** after approval

---

## Key Conventions

### Code Style

**General Principles:**
- Write clean, self-documenting code
- Follow DRY (Don't Repeat Yourself)
- Prefer readability over cleverness
- Use meaningful variable and function names

**To Be Established:**
- Linting rules (ESLint, Prettier, etc.)
- Naming conventions for files and functions
- Component structure patterns
- State management patterns

### File Naming

**Recommended Conventions:**
- Use kebab-case for directories: `weather-data/`
- Component files: PascalCase (e.g., `WeatherCard.jsx`)
- Utility files: camelCase (e.g., `formatTemperature.js`)
- Test files: `*.test.js` or `*.spec.js`

### Documentation

**Code Comments:**
- Use comments for "why", not "what"
- Document complex algorithms
- Add JSDoc/TSDoc for public APIs

**README Updates:**
- Keep README.md current with project setup instructions
- Include prerequisites, installation, and running instructions

---

## Technology Stack

### To Be Determined
The following should be documented once established:

**Frontend:**
- Framework: (React, Vue, Svelte, Next.js, etc.)
- Styling: (CSS Modules, Tailwind, styled-components, etc.)
- Build tools: (Vite, Webpack, etc.)

**Backend (if applicable):**
- Runtime: (Node.js, Python, etc.)
- Framework: (Express, FastAPI, etc.)
- Database: (PostgreSQL, MongoDB, etc.)

**Weather Data Sources:**
- APIs to be integrated
- Data update frequency
- Caching strategy

**Deployment:**
- Hosting platform
- CI/CD pipeline
- Environment management

---

## Common Development Tasks

### Setting Up Development Environment

```bash
# Clone the repository
git clone <repository-url>
cd weatherdataexplained.com

# Install dependencies (once package.json exists)
# npm install  # or yarn install, pnpm install

# Start development server
# npm run dev  # or appropriate command
```

### Running Tests

```bash
# Run all tests (once testing is set up)
# npm test

# Run tests in watch mode
# npm test -- --watch

# Run tests with coverage
# npm test -- --coverage
```

### Building for Production

```bash
# Create production build
# npm run build

# Preview production build
# npm run preview
```

---

## Testing and Quality Assurance

### Testing Strategy (To Be Established)

**Unit Tests:**
- Test individual functions and components
- Aim for high coverage of utility functions
- Mock external dependencies

**Integration Tests:**
- Test component interactions
- Test API integrations
- Verify data flow

**E2E Tests:**
- Test critical user journeys
- Verify complete workflows

### Code Quality Tools

**To Be Configured:**
- Linter (ESLint)
- Formatter (Prettier)
- Type checking (TypeScript/JSDoc)
- Pre-commit hooks (Husky)

---

## Weather Data Considerations

### Data Sources
Document the following as they're integrated:
- Primary weather API(s)
- Data update frequency
- API rate limits
- Authentication requirements
- Fallback data sources

### Data Processing
- Temperature units (Celsius, Fahrenheit, Kelvin)
- Pressure units (hPa, inHg, mmHg)
- Wind speed units (m/s, km/h, mph, knots)
- Precipitation units (mm, inches)
- Data validation and error handling

### Educational Content
- Explanation of weather phenomena
- Visualization best practices
- Accessibility for different knowledge levels
- Multi-language support (if applicable)

---

## AI Assistant Guidelines

### Before Starting Work

1. **Understand the task** - Read the issue or request carefully
2. **Check existing code** - Review related files and patterns
3. **Plan your approach** - Use TodoWrite for multi-step tasks
4. **Ask clarifying questions** - If requirements are unclear

### During Development

1. **Use TodoWrite** - Track progress on complex tasks
2. **Follow conventions** - Match existing code style
3. **Test changes** - Verify functionality works as expected
4. **Check for errors** - Run linters, tests before committing
5. **Security awareness** - Avoid XSS, injection vulnerabilities, API key exposure

### Code Quality Checklist

- [ ] Code follows project conventions
- [ ] No security vulnerabilities introduced
- [ ] Error handling is appropriate
- [ ] Edge cases are considered
- [ ] Code is well-documented
- [ ] Tests are added/updated
- [ ] No console.log or debugging code left
- [ ] Dependencies are justified and documented

### Committing Changes

1. **Stage relevant files only** - Don't commit unrelated changes
2. **Write clear commit messages** - Follow the format above
3. **Review changes** - Check `git diff` before committing
4. **Don't commit secrets** - API keys, credentials, .env files
5. **Push to feature branch** - Use `git push -u origin <branch-name>`

### Creating Pull Requests

**PR Title Format:**
```
<type>: Brief description of changes
```

**PR Description Template:**
```markdown
## Summary
- Brief bullet points of what changed
- Why the changes were made

## Implementation Details
- Key technical decisions
- Files modified
- Dependencies added/removed

## Test Plan
- [ ] Manual testing steps completed
- [ ] Automated tests pass
- [ ] Verified on different browsers/devices (if applicable)

## Screenshots
(If UI changes)

## Additional Notes
(Optional context or considerations)
```

---

## Project-Specific Notes

### Weather Data Explanation Focus

This project aims to make weather data accessible and understandable. Keep in mind:

- **Target Audience:** May include users with varying technical backgrounds
- **Educational Value:** Prioritize clear explanations over complexity
- **Visualizations:** Should be intuitive and informative
- **Accuracy:** Weather data must be accurately represented
- **Performance:** Data fetching should be efficient and cached appropriately

### Accessibility

- Follow WCAG 2.1 AA standards
- Ensure proper semantic HTML
- Support keyboard navigation
- Provide text alternatives for visualizations
- Test with screen readers

### Performance

- Optimize API calls (caching, batching)
- Lazy load non-critical resources
- Optimize images and assets
- Consider offline functionality
- Monitor bundle size

---

## Resources and References

### Documentation (To Be Added)
- Architecture decision records (ADRs)
- API documentation
- Component library documentation
- Deployment guide

### External Resources
- Weather API documentation (once selected)
- Framework documentation
- Design system (if applicable)

---

## Getting Help

### For AI Assistants
- Reference this file before starting work
- Check README.md for project-specific setup
- Review recent commits for coding patterns
- Use Task tool for codebase exploration

### For Human Developers
- Check GitHub Issues for known problems
- Review Pull Requests for ongoing work
- Contact repository maintainer: marek-rodny

---

## Changelog

### 2025-11-20
- Initial CLAUDE.md created
- Documented repository structure and guidelines
- Established development workflow conventions
- Set up AI assistant guidelines

---

**Last Updated:** 2025-11-20
**Version:** 1.0.0
**Maintained By:** Project contributors

---

## Notes for Future Updates

As the project evolves, update this file with:
- [ ] Actual technology stack once chosen
- [ ] Specific coding standards and linting rules
- [ ] API integration details
- [ ] Deployment procedures
- [ ] Common troubleshooting issues
- [ ] Performance benchmarks
- [ ] Testing coverage requirements
