# Project Overview
This project is an MCP (Model Context Protocol) server that allows Claude to interact with internal company data
such as:
- Workspaces
- Deficiencies
- Tasks
- Assets
- Work Orders
- Activity
- Teams
- Accounts

It exposes a set of tools, which are API endpoints to Claude, so Claude can call and retrieve structured data and perform
queries. This enables a conversational style interface that allows users to get answers and insights into their operational data.

## Features:

###Authentication
- Authenticate each API call using user credentials
- Get TGT -> ST -> Session
- Ensure users are authroized to see data
- Respond with "Not Authorized" message in the case that a user is not authorized

###Workspace Tools
- Takes in workspace name
- Fetch all assets in a workspace
- Get the activity feed from any workspace
- Find tasks in workspaces

###Deficiency Tools
- Get details for deficiencies in workspaces
- Find if deficiencies have related tasks
- Get more information on deficiencies

###Tasks


### Tool2:


### Tool3:
- ipsum

### Tool4









  
