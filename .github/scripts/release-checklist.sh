#!/bin/bash

echo "🚀 Release Checklist"
echo "1. ✅ All features tested and ready?"
echo "2. ✅ Documentation updated?"
echo "3. ✅ Breaking changes documented?"
echo "4. ✅ Security review completed?"
echo "5. ✅ Performance testing done?"
echo ""
echo "Ready to create release branch? (y/n)"
read -r response
if [[ $response == "y" ]]; then
	echo "🌟 Creating release branch..."
	git checkout main && git pull
	echo "Enter version (e.g., 1.2.0):"
	read -r version
	git checkout -b "release-v$version"
	echo "✨ Release branch release-v$version created!"
	echo "Next steps:"
	echo "1. Cherry-pick commits: git cherry-pick <hash>"
	echo "2. Push branch: git push origin release-v$version"
	echo "3. Create PR to main"
fi
