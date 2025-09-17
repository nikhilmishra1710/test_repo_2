import logging

logging.debug("hel lo world")
logging.debug("Byee world logging.debug('Byee world')")

logging.info("This is a    test log")


"""
- name: Create Jira release version
        if: success()
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_URL }}
          JIRA_PROJECT: ${{ secrets.JIRA_PROJECT_KEY }}
          JIRA_USER: ${{ secrets.JIRA_EMAIL }}
          JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}
        run: |
          echo "Creating Jira release for tag $NEW_TAG"

          jq -n \
            --arg project "$JIRA_PROJECT" \
            --arg name "$NEW_TAG" \
            --arg desc "Release created from GitHub tag $NEW_TAG" \
            '{
              name: $name,
              description: $desc,
              released: true,
              project: $project
            }' > version.json

          RESPONSE=$(curl -s -o response.json -w "%{http_code}" \
            -u "$JIRA_USER:$JIRA_TOKEN" \
            -H "Content-Type: application/json" \
            -X POST \
            --data @version.json \
            "$JIRA_BASE_URL/rest/api/3/version")

          echo "HTTP Response: $RESPONSE"
          cat response.json

      - name: Extract Jira version ID
        run: |
          VERSION_ID=$(jq -r '.id' response.json)
          echo "VERSION_ID=$VERSION_ID" >> $GITHUB_ENV

      - name: Link Jira issues to release
        if: success()
        env:
          JIRA_BASE_URL: ${{ secrets.JIRA_URL }}
          JIRA_PROJECT: ${{ secrets.JIRA_PROJECT_KEY }}
          JIRA_USER: ${{ secrets.JIRA_EMAIL }}
          JIRA_TOKEN: ${{ secrets.JIRA_TOKEN }}
          VERSION_ID: ${{ env.VERSION_ID }}
          PR_TITLE: ${{ github.event.pull_request.title }}
        run: |
          echo "Looking for Jira issue keys in PR title: $PR_TITLE"
          ISSUE_KEYS=$(echo "$PR_TITLE" | grep -oE "$JIRA_PROJECT-[0-9]+" || true)
          echo "Issue keys: $ISSUE_KEYS"
          for ISSUE in $ISSUE_KEYS; do
            echo "Linking $ISSUE to version $VERSION_ID"
            curl -s -o link_response.json -w "%{http_code}" \
              -u "$JIRA_USER:$JIRA_TOKEN" \
              -H "Content-Type: application/json" \
              -X PUT \
              --data "{\"update\": {\"fixVersions\": [{\"add\": {\"id\": \"$VERSION_ID\"}}]}}" \
              "$JIRA_BASE_URL/rest/api/3/issue/$ISSUE"
          done

"""