# Branch Protection Rules

The `main` branch must be protected with the following rules (configured manually in GitHub Settings):

1. **Require pull request reviews before merging**:
   - Required approving reviews: 1
   - Dismiss stale pull request approvals when new commits are pushed: true
2. **Require status checks to pass before merging**:
   - Require branches to be up to date before merging: true
   - Status checks required:
     - `lint`
     - `typecheck`
     - `test`
     - `Analyze (javascript-typescript)`
     - `Analyze (python)`
3. **Require signed commits**: true
4. **Require linear history**: true
5. **Do not allow bypassing the above settings**: true
