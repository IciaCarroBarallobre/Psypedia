export interface ConversationTurn {
  role: 'user' | 'assistant'
  content: string
}

export interface Source {
  title: string
  url: string
}

export interface ChatReply {
  content: string
  sources: Source[]
}

export interface Message {
  id: number
  role: 'user' | 'assistant'
  content: string
  sources?: Source[]
}
