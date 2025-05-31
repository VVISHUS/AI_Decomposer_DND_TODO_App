import React, { useState } from 'react';
import axios from 'axios';
import { 
  DndContext, 
  KeyboardSensor, 
  PointerSensor, 
  useSensor, 
  useSensors,
  DragOverlay,
  defaultDropAnimation,
  useDroppable
} from '@dnd-kit/core';
import { 
  SortableContext, 
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable
} from '@dnd-kit/sortable';
import "../src/App.css";
import { CSS } from '@dnd-kit/utilities';
import { rectIntersection } from '@dnd-kit/core';
import { ToastContainer, toast } from 'react-toastify';
import 'react-toastify/dist/ReactToastify.css';

const MODEL_KEYS = [
  "llama-3.3_70B",
  "llama-3.1_8B⚡",
  // "hermes-3_70B",
  // "qwq_32B",
  "deepseek-v3",
  // "qwq_32B_alt",
  "deepseek-v3_0324",
  // "deepseek-r1",
  "qwen2.5-coder_32B",
  "llama-3.2_3B⚡",
  "qwen2.5_72B",
  "llama-3_70B⚡",
  // "llama-3.1_405B",
  "llama-3.1_70B",
  "gemini-1.5-flash⚡"
];


const Notification = () => (
  <ToastContainer
    position="top-right"
    autoClose={5000}
    hideProgressBar={false}
    newestOnTop={false}
    closeOnClick
    rtl={false}
    pauseOnFocusLoss
    draggable
    pauseOnHover
    theme="light"
  />
);


const EditableText = ({ value, onChange, className, placeholder }) => {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(value);

  const handleDoubleClick = () => {
    setIsEditing(true);
  };

  const handleChange = (e) => {
    setEditValue(e.target.value);
  };

  const handleBlur = () => {
    setIsEditing(false);
    if (editValue !== value) {
      onChange(editValue);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault(); // Add this line to prevent form submission
      handleBlur();
    }
  };

  return isEditing ? (
    <input
      type="text"
      value={editValue}
      onChange={handleChange}
      onBlur={handleBlur}
      onKeyDown={handleKeyDown}
      autoFocus
      className={className}
      placeholder={placeholder}
    />
  ) : (
    <div 
      onDoubleClick={handleDoubleClick}
      className={className}
    >
      {value || placeholder}
    </div>
  );
};

const SortableItem = ({ id, children, onUpdateTask }) => {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging
  } = useSortable({ id });

  const style = {
    transform: transform ? CSS.Transform.toString(transform) : undefined,
    transition,
    opacity: isDragging ? 0.5 : 1,
    zIndex: isDragging ? 1000 : 'auto'
  };

  return (
    <div 
      ref={setNodeRef} 
      style={style}
      {...attributes}
      {...listeners}
    >
      {children}
    </div>
  );
};

const TaskCard = ({ task, onUpdateTask }) => {
  const handleTaskUpdate = (newContent) => {
    onUpdateTask({
      ...task,
      content: newContent
    });
  };

  const handleStepUpdate = (stepId, newContent) => {
    onUpdateTask({
      ...task,
      steps: task.steps.map(step => 
        step.id === stepId ? { ...step, content: newContent } : step
      )
    });
  };

  const handleAddStep = (e) => {
    e.preventDefault(); // Add this line to prevent form submission
    const newStep = {
      id: `step-${Date.now()}`,
      content: ''
    };
    onUpdateTask({
      ...task,
      steps: [...(task.steps || []), newStep]
    });
  };

  return (
    <div className="task-card">
      <EditableText
        value={task.content}
        onChange={handleTaskUpdate}
        className="task-title"
        placeholder="Task title"
      />
      {task.steps && task.steps.length > 0 && (
        <ul className="task-steps">
          {task.steps.map(step => (
            <li key={step.id}>
              <EditableText
                value={step.content}
                onChange={(newContent) => handleStepUpdate(step.id, newContent)}
                className="step-content"
                placeholder="Subtask"
              />
            </li>
          ))}
          <li>
            <button onClick={handleAddStep} className="add-step-btn" type="button">
              + Add Subtask
            </button>
          </li>
        </ul>
      )}
      {(!task.steps || task.steps.length === 0) && (
        <button onClick={handleAddStep} className="add-step-btn" type="button">
          + Add First Subtask
        </button>
      )}
    </div>
  );
};


const AddTaskButton = ({ columnId, onAddTask }) => {
  const [isAdding, setIsAdding] = useState(false);
  const [taskContent, setTaskContent] = useState('');
  const [subtasks, setSubtasks] = useState(['']);

  const handleAddClick = () => {
    setIsAdding(true);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!taskContent.trim()) return;

    const newTask = {
      id: `task-${Date.now()}`,
      content: taskContent,
      steps: subtasks.filter(s => s.trim()).map((content, index) => ({
        id: `step-${Date.now()}-${index}`,
        content
      }))
    };

    onAddTask(columnId, newTask);
    setTaskContent('');
    setSubtasks(['']);
    setIsAdding(false);
  };

  const handleAddSubtask = () => {
    setSubtasks([...subtasks, '']);
  };

  const handleSubtaskChange = (index, value) => {
    const newSubtasks = [...subtasks];
    newSubtasks[index] = value;
    setSubtasks(newSubtasks);
  };

  if (isAdding) {
    return (
      <form onSubmit={handleSubmit} className="add-task-form">
        <input
          type="text"
          value={taskContent}
          onChange={(e) => setTaskContent(e.target.value)}
          placeholder="Task title"
          autoFocus
        />
        {subtasks.map((subtask, index) => (
          <input
            key={index}
            type="text"
            value={subtask}
            onChange={(e) => handleSubtaskChange(index, e.target.value)}
            placeholder={`Subtask ${index + 1}`}
          />
        ))}
        <button type="button" onClick={handleAddSubtask} className="add-subtask-btn">
          + Add Subtask
        </button>
        <div className="form-actions">
          <button type="submit" className="save-btn">Save</button>
          <button type="button" onClick={() => setIsAdding(false)} className="cancel-btn">
            Cancel
          </button>
        </div>
      </form>
    );
  }

  return (
    <button className="add-task-btn" onClick={handleAddClick}>
      + Add Task
    </button>
  );
};

const Column = ({ id, title, items, onAddTask, onUpdateTask }) => {
  const { setNodeRef, isOver } = useDroppable({ 
    id,
    data: {
      type: 'column',
      columnId: id
    }
  });
  
  return (
    <div 
      ref={setNodeRef} 
      className={`column ${isOver ? 'hovered' : ''}`}
      style={{
        position: 'relative',
        minHeight: '300px'
      }}
    >
      <h2>{title}</h2>
      <SortableContext
        items={items}
        strategy={verticalListSortingStrategy}
      >
        <div className="tasks">
          {items.map(task => (
            <SortableItem key={task.id} id={task.id} onUpdateTask={onUpdateTask}>
              <TaskCard task={task} onUpdateTask={onUpdateTask} />
            </SortableItem>
          ))}
        </div>
      </SortableContext>
      <AddTaskButton columnId={id} onAddTask={onAddTask} />
    </div>
  );
};

function App() {
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [activeId, setActiveId] = useState(null);
  const [selectedModel, setSelectedModel] = useState("gemini-1.5-flash");
  const [columns, setColumns] = useState({
    'todo': { id: 'todo', title: 'To Do', items: [] },
    'in-progress': { id: 'in-progress', title: 'In Progress', items: [] },
    'done': { id: 'done', title: 'Done', items: [] }
  });

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
  // Validate input length
  if (input.trim().length < 5) {
    toast.error('Please enter at least 5 characters for your goal');
    return;
  }
    setIsLoading(true);
    try {
      const apiUrl = process.env.REACT_APP_API_URL;
      const cleanModel = selectedModel.replace(/[\u231A-\uD83E\uDDFF\u2600-\u26FF\u2700-\u27BF]/g, "").trim();
      const response = await axios.post(apiUrl, {
        model: cleanModel,
        query: input
      });
      
      // Check for API-level errors
      if (response.data.status === "error") {
        throw new Error(response.data.message || 'Failed to process your request');
      }

      // Validate response structure
      if (!response.data.data || typeof response.data.data !== 'object') {
        throw new Error('Invalid response format from server');
      }

      const subtasks = response.data.data;
      const newTasks = [];
      let subtaskCounter = 1;
      
      for (const [subtaskKey, subtaskData] of Object.entries(subtasks)) {
        // Validate subtask structure
        if (!subtaskData || typeof subtaskData !== 'object' || 
            !subtaskData.title || !subtaskData.steps) {
          console.warn(`Skipping invalid subtask: ${subtaskKey}`);
          continue;
        }

        const taskId = `task-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`;
        
        // Convert steps to array format with proper numbering
        const taskSteps = Object.entries(subtaskData.steps).map(([stepKey, stepContent], index) => ({
          id: `step-${taskId}-${index + 1}`,
          content: `${stepContent}`
        }));
        
        // Add numbering to subtask title if not already present
        const subtaskTitle = subtaskData.title.startsWith(`${subtaskCounter}.`) 
          ? subtaskData.title 
          : `${subtaskCounter}. ${subtaskData.title}`;
        
        newTasks.push({
          id: taskId,
          content: subtaskTitle,
          steps: taskSteps
        });
        
        subtaskCounter++;
      }
      
      if (newTasks.length === 0) {
        throw new Error('No valid tasks were created from the response');
      }
      
      setColumns(prevColumns => ({
        ...prevColumns,
        'todo': {
          ...prevColumns['todo'],
          items: [...prevColumns['todo'].items, ...newTasks]
        }
      }));
      
      setInput('');
      toast.success(`Created ${newTasks.length} tasks successfully using ${selectedModel}!`);
    } catch (error) {
      console.error('Error:', error);
      toast.error(error.message || 'Failed to create tasks');
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddTask = (columnId, newTask) => {
    setColumns(prevColumns => ({
      ...prevColumns,
      [columnId]: {
        ...prevColumns[columnId],
        items: [...prevColumns[columnId].items, newTask]
      }
    }));
  };

  const handleUpdateTask = (updatedTask) => {
    setColumns(prevColumns => {
      const newColumns = { ...prevColumns };
      for (const columnId in newColumns) {
        const taskIndex = newColumns[columnId].items.findIndex(t => t.id === updatedTask.id);
        if (taskIndex !== -1) {
          newColumns[columnId].items[taskIndex] = updatedTask;
          break;
        }
      }
      return newColumns;
    });
  };

  const handleDragStart = (event) => {
    setActiveId(event.active.id);
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    setActiveId(null);

    if (!over) return;

    const activeContainer = findContainer(active.id);
    const overContainer = findContainer(over.id) || over.data?.current?.columnId;

    if (!activeContainer || !overContainer) return;
    if (activeContainer === overContainer) return;

    setColumns(prevColumns => {
      const activeColumn = prevColumns[activeContainer];
      const overColumn = prevColumns[overContainer];
      
      if (!activeColumn || !overColumn) return prevColumns;

      const activeItem = activeColumn.items.find(item => item.id === active.id);
      if (!activeItem) return prevColumns;

      return {
        ...prevColumns,
        [activeContainer]: {
          ...activeColumn,
          items: activeColumn.items.filter(item => item.id !== active.id)
        },
        [overContainer]: {
          ...overColumn,
          items: [...overColumn.items, activeItem]
        }
      };
    });
  };

  const handleDragCancel = () => {
    setActiveId(null);
  };

  const findContainer = (id) => {
    if (columns[id]) return id;
    
    for (const [columnId, column] of Object.entries(columns)) {
      if (column.items.some(item => item.id === id)) {
        return columnId;
      }
    }
    
    return null;
  };

  const findTaskContent = (taskId) => {
    for (const column of Object.values(columns)) {
      const task = column.items.find(item => item.id === taskId);
      if (task) {
        return (
          <div className="task-card dragging">
            <h3>{task.content}</h3>
            {task.steps && task.steps.length > 0 && (
              <ul className="task-steps">
                {task.steps.map(step => (
                  <li key={step.id}>{step.content}</li>
                ))}
              </ul>
            )}
          </div>
        );
      }
    }
    return null;
  };

   return (
    <div className="app">
      <Notification />
      <header className="app-header">
        <h1>LLM-Powered Task Tracker</h1>
        <form onSubmit={handleSubmit} className="task-input-form">
          <div className="model-selector">
            <label htmlFor="model-select">Model: </label>
            <select
              id="model-select"
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              disabled={isLoading}
            >
              {MODEL_KEYS.map((modelKey) => (
                <option key={modelKey} value={modelKey}>
                  {modelKey}
                </option>
              ))}
            </select>
          </div>
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Enter your goal"
            disabled={isLoading}
          />
          <button 
            type="submit" 
            disabled={isLoading || !input.trim() || input.trim().length < 5}
          >
            {isLoading ? 'Processing...' : 'Create Tasks'}
          </button>
        </form>
      </header>

      <div className="board">
        <DndContext
          sensors={sensors}
          collisionDetection={rectIntersection}
          onDragStart={handleDragStart}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
          modifiers={[
            ({ transform }) => ({
              ...transform,
              scaleX: 1,
              scaleY: 1
            })
          ]}
        >
          <div className="columns">
            {Object.values(columns).map(column => (
              <Column
                key={column.id}
                id={column.id}
                title={column.title}
                items={column.items}
                onAddTask={handleAddTask}
                onUpdateTask={handleUpdateTask}
              />
            ))}
          </div>
          <DragOverlay dropAnimation={defaultDropAnimation}>
            {activeId ? findTaskContent(activeId) : null}
          </DragOverlay>
        </DndContext>
      </div>
    </div>

    
  );
}

export default App;