# Document Management MCP Server

A simple document management server built with the official **Model Context Protocol (MCP) Python SDK**.

This project is being developed alongside the **Claude Academy — Introduction to Model Context Protocol** course to understand how MCP servers, tools, clients, and the MCP Inspector work together.

---

## 📚 Learning Project

This repository follows the concepts taught in:

**Claude Academy — Introduction to Model Context Protocol**

The goal is not just to complete the course, but to implement each concept in a working MCP project and maintain it as a practical reference.

---

## 🏗️ Project Overview

This project implements an MCP server that provides tools for reading and editing documents.

Currently, documents are stored in memory using a Python dictionary.

### Current Architecture

```text
┌─────────────────────┐
│    MCP Client       │
│                     │
│  MCP Inspector      │
└──────────┬──────────┘
           │
           │ MCP / STDIO
           ▼
┌─────────────────────┐
│   DocumentMCP       │
│                     │
│   Python Server     │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ In-Memory Documents │
│                     │
│ Python Dictionary   │
└─────────────────────┘

![Architecture Diagram](src/docs/images/image.png)


## MCP Inspector 

![alt text](image-1.png)

![alt text](image-2.png)

![alt text](image-3.png)

## MCP Client 

![alt text](image-4.png)


## Defining Resources

![alt text](image.png)

![alt text](image-1.png)


## Accessing Resources

![alt text](image-2.png)

## Prompts

### Server side Prompt 

![alt text](image-3.png)


### Client side Prompt

![alt text](image-5.png)

## Sampling 

                 MCP
┌──────────────┐       ┌──────────────┐
│ MCP Server   │       │ MCP Client   │
│              │       │              │
│ summarize()  │       │              │
│      │       │       │              │
│      │ create_message()            │
│      ├────────────────────────────►│
│              │       │ sampling    │
│              │       │ callback    │
│              │       │      │       │
│              │       │      ▼       │
│              │       │   Claude    │
│              │       │      │       │
│              │       │      ▼       │
│              │◄─────────────────────┤
│      │       │       │              │
│      ▼       │       │              │
│  summary     │       │              │
└──────────────┘       └──────────────┘


## Log and Notification 

![alt text](image-6.png)

## Roots 

![alt text](image-7.png)

# Complete Model of the following features 

TOOLS
Server → Client
"Here's functionality you can call."


RESOURCES
Server → Client
"Here's data you can read."


PROMPTS
Server → Client
"Here's a reusable prompt."


SAMPLING
Server → Client → LLM → Client → Server
"Ask the client's LLM to generate something."


LOGGING / PROGRESS
Server → Client
"Here's what's happening while I'm working."


ROOTS
Client → Server
"These filesystem locations are in scope."


## Json Message types

                 MCP Connection
              ┌──────────────────┐
              │                  │
Client  ◄─────┤   Bidirectional  ├─────► Server
              │                  │
              └──────────────────┘


Client → Server

initialize
tools/list
tools/call
resources/read

Server
  │
  │ CreateMessage Request
  ↓
Client
  │
  │ Sampling Result
  ↓
Server

             ┌─────────────────────┐
             │    MCP Connection   │
             └─────────────────────┘

Client ───────────────► Server
       tools/call

Client ◄────────────── Server
       sampling

Client ◄────────────── Server
       roots

Client ◄────────────── Server
       logging

Client ◄────────────── Server
       progress


![alt text](image-8.png)  

