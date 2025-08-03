/**
 * Tasks page - Task execution and management
 */

import { createFileRoute } from '@tanstack/react-router';
import { useState } from 'react';
import { useAtom } from 'jotai';
import { 
  selectedAgentTypeAtom, 
  taskHistoryAtom,
  filteredTaskHistoryAtom,
  taskFilterAtom
} from '../stores/atoms';
import { useExecuteTask } from '../hooks/useApi';
import type { TaskRequest } from '../types/api';
import { 
  Play, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Filter,
  Bot,
  Database,
  Brain
} from 'lucide-react';

function TasksPage() {
  const [selectedAgentType, setSelectedAgentType] = useAtom(selectedAgentTypeAtom);
  const [taskHistory] = useAtom(taskHistoryAtom);
  const [filteredTasks] = useAtom(filteredTaskHistoryAtom);
  const [taskFilter, setTaskFilter] = useAtom(taskFilterAtom);
  
  const [taskForm, setTaskForm] = useState({
    name: '',
    data: '',
  });

  const executeTaskMutation = useExecuteTask();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!taskForm.name.trim()) {
      alert('Please enter a task name');
      return;
    }

    let parsedData: Record<string, any> = {};
    
    try {
      if (taskForm.data.trim()) {
        parsedData = JSON.parse(taskForm.data);
      }
    } catch (error) {
      alert('Invalid JSON format in task data');
      return;
    }

    // Set default data based on agent type
    if (selectedAgentType === 'llm') {
      parsedData = {
        messages: parsedData.messages || [
          { role: 'user', content: taskForm.name }
        ],
        temperature: parsedData.temperature || 0.7,
        max_tokens: parsedData.max_tokens || 1000,
        ...parsedData
      };
    } else if (selectedAgentType === 'database') {
      parsedData = {
        query: parsedData.query || taskForm.name,
        category: parsedData.category,
        limit: parsedData.limit || 5,
        ...parsedData
      };
    } else if (selectedAgentType === 'rag') {
      parsedData = {
        question: parsedData.question || taskForm.name,
        ...parsedData
      };
    }

    const request: TaskRequest = {
      name: taskForm.name,
      agent_type: selectedAgentType,
      data: parsedData,
    };

    executeTaskMutation.mutate(request);
    
    // Reset form
    setTaskForm({ name: '', data: '' });
  };

  const getAgentIcon = (type: string) => {
    switch (type) {
      case 'llm':
        return <Bot className="w-5 h-5" />;
      case 'database':
        return <Database className="w-5 h-5" />;
      case 'rag':
        return <Brain className="w-5 h-5" />;
      default:
        return <Bot className="w-5 h-5" />;
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-500" />;
      default:
        return <Clock className="w-4 h-4 text-yellow-500" />;
    }
  };

  const getDefaultDataExample = (agentType: string) => {
    switch (agentType) {
      case 'llm':
        return `{
  "messages": [
    {"role": "user", "content": "Your prompt here"}
  ],
  "temperature": 0.7,
  "max_tokens": 1000
}`;
      case 'database':
        return `{
  "query": "search terms",
  "category": "optional category",
  "limit": 5
}`;
      case 'rag':
        return `{
  "question": "Your question here"
}`;
      default:
        return '{}';
    }
  };

  return (
    <div className="px-4 py-6 sm:px-0">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">Tasks</h1>
        <p className="mt-2 text-gray-600">
          Execute tasks using different AI agent types
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Task Execution Form */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Execute New Task</h2>
          
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Agent Type Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-3">
                Select Agent Type
              </label>
              <div className="grid grid-cols-3 gap-3">
                {(['llm', 'database', 'rag'] as const).map((type) => (
                  <button
                    key={type}
                    type="button"
                    onClick={() => setSelectedAgentType(type)}
                    className={`p-3 border rounded-lg flex flex-col items-center space-y-2 transition-colors ${
                      selectedAgentType === type
                        ? 'border-blue-500 bg-blue-50 text-blue-700'
                        : 'border-gray-300 text-gray-600 hover:border-gray-400'
                    }`}
                  >
                    {getAgentIcon(type)}
                    <span className="text-sm font-medium capitalize">{type}</span>
                  </button>
                ))}
              </div>
            </div>

            {/* Task Name */}
            <div>
              <label htmlFor="taskName" className="block text-sm font-medium text-gray-700 mb-2">
                Task Name
              </label>
              <input
                id="taskName"
                type="text"
                value={taskForm.name}
                onChange={(e) => setTaskForm({ ...taskForm, name: e.target.value })}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                placeholder="Enter task description..."
                required
              />
            </div>

            {/* Task Data */}
            <div>
              <label htmlFor="taskData" className="block text-sm font-medium text-gray-700 mb-2">
                Task Data (JSON)
              </label>
              <textarea
                id="taskData"
                value={taskForm.data}
                onChange={(e) => setTaskForm({ ...taskForm, data: e.target.value })}
                rows={8}
                className="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 font-mono text-sm"
                placeholder={getDefaultDataExample(selectedAgentType)}
              />
              <p className="mt-2 text-sm text-gray-500">
                Leave empty to use default configuration for {selectedAgentType} agent
              </p>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={executeTaskMutation.isPending}
              className="w-full flex items-center justify-center px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {executeTaskMutation.isPending ? (
                <>
                  <Clock className="w-4 h-4 mr-2 animate-spin" />
                  Executing...
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 mr-2" />
                  Execute Task
                </>
              )}
            </button>
          </form>
        </div>

        {/* Task History */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h3 className="text-lg font-medium text-gray-900">Task History</h3>
              <div className="flex items-center space-x-2">
                <Filter className="w-4 h-4 text-gray-400" />
                <select
                  value={taskFilter}
                  onChange={(e) => setTaskFilter(e.target.value as any)}
                  className="text-sm border border-gray-300 rounded px-2 py-1"
                >
                  <option value="all">All Tasks</option>
                  <option value="completed">Completed</option>
                  <option value="failed">Failed</option>
                </select>
              </div>
            </div>
          </div>
          
          <div className="p-6">
            {filteredTasks.length === 0 ? (
              <div className="text-center text-gray-500 py-8">
                {taskHistory.length === 0 ? 'No tasks executed yet' : 'No tasks match the filter'}
              </div>
            ) : (
              <div className="space-y-4 max-h-96 overflow-y-auto">
                {filteredTasks.map((task) => (
                  <div key={task.task_id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center space-x-2 mb-2">
                          {getStatusIcon(task.status)}
                          <span className="font-medium text-gray-900">{task.name}</span>
                          <span className="text-xs bg-gray-100 px-2 py-1 rounded">
                            {task.task_id.split('_')[0]}...
                          </span>
                        </div>
                        
                        <div className="text-sm text-gray-600 mb-2">
                          Created: {new Date(task.created_at).toLocaleString()}
                          {task.completed_at && (
                            <span className="ml-4">
                              Completed: {new Date(task.completed_at).toLocaleString()}
                            </span>
                          )}
                        </div>

                        {task.result && (
                          <div className="mt-2 p-2 bg-green-50 border border-green-200 rounded text-sm">
                            <strong>Result:</strong> {
                              typeof task.result === 'string' 
                                ? task.result.substring(0, 200) + (task.result.length > 200 ? '...' : '')
                                : JSON.stringify(task.result).substring(0, 200) + '...'
                            }
                          </div>
                        )}

                        {task.error && (
                          <div className="mt-2 p-2 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                            <strong>Error:</strong> {task.error}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export const Route = createFileRoute('/tasks')({
  component: TasksPage,
});