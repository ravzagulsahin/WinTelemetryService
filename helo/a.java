import java.util.*;

public class Lab12 {

    public static void main(String[] args) {
        Graph<Integer> g = new Graph<>();

        g.addEdge(1,2); g.addEdge(1,3); g.addEdge(2,4);
        g.addEdge(3,4); g.addEdge(4,5); g.addEdge(5,6);
        g.addNode(10);

        System.out.println(g.bfs(1));
        System.out.println(g.dfs(1));
        System.out.println(g.getShortestPath(1,6));

        g.removeEdge(4,5);
        System.out.println(g.getShortestPath(1,6));

        g.removeNode(3);
        System.out.println(g.bfs(1));

        System.out.println(g.getShortestPath(10,1));
    }
}

interface IUndirectedNode<T> {
    void addNeighbor(Node<T> neighbor);
    void removeNeighbor(Node<T> neighbor);
}


class Node<T> implements IUndirectedNode<T> {
    T data;
    List<Node<T>> neighbors;

    // BFS helper fields for easier implementation for shortest path method
    boolean visited;
    Node<T> parent;

    public Node(T data) {
        this.data = data;
        this.neighbors = new ArrayList<>();
    }

    @Override
    public void addNeighbor(Node<T> neighbor) {
        if(!neighbors.contains(neighbor)) neighbors.add(neighbor);
    }

    @Override
    public void removeNeighbor(Node<T> neighbor) {
        neighbors.remove(neighbor);
    }


    @Override
    public String toString() {
        return data.toString();
    }
}


interface AdjacencyList<T> {
    void addNode(T node);
    void addEdge(T data1, T data2);
    void removeNode(T data);
    void removeEdge(T data1, T data2);
    List<T> bfs(T startData);
    List<T> dfs(T startData);
    List<T> getShortestPath(T startData, T endData);
}

class Graph<T> implements AdjacencyList<T> {
    private Map<T, Node<T>> nodes;

    public Graph() {
        this.nodes = new HashMap<>();
    }


    @Override
    public void addNode(T data) {
        /*
         * TODO:
         * Add a new node if it does not already exist.
         * Store it inside nodes.
         */
        
        if(!nodes.containsKey(data)) nodes.put(data,new Node<>(data));
    }

    @Override
    public void addEdge(T data1, T data2) {
        /*
         * TODO:
         * Ensure both nodes exist (create if needed).
         * Add each node as a neighbor to the other (undirected graph).
         */
        
        addNode(data1);
        addNode(data2);
        Node<T> n1 = nodes.get(data1);
        Node<T> n2 = nodes.get(data2);
        n1.addNeighbor(n2);
        n2.addNeighbor(n1);
    }

    @Override
    public void removeEdge(T data1, T data2) {
        /*
         * TODO:
         * If both nodes exist:
         * - Remove data2 from data1's neighbor list
         * - Remove data1 from data2's neighbor list
         */
        
        if(!nodes.containsKey(data1) || !nodes.containsKey(data2)) return;
        Node<T> n1 = nodes.get(data1);
        Node<T> n2 = nodes.get(data2);
        n1.removeNeighbor(n2);
        n2.removeNeighbor(n1);
    }

    @Override
    public void removeNode(T data) {
        /*
         * TODO:
         * If node exists:
         * - Remove this node from all neighbor lists
         * - Remove the node from nodes
         */
        
        if(!nodes.containsKey(data)) return;
        Node<T> t = nodes.get(data);
        ArrayList<Node<T>> nodeList = new ArrayList<>(nodes.values());
        for(int i = 0; i<nodeList.size();i++) nodeList.get(i).removeNeighbor(t);
        nodes.remove(data);
    }

    @Override
    public List<T> bfs(T startData) {
        /*
         * TODO:
         * Perform Breadth-First Search starting from startData.
         *
         * Steps:
         * 1. Get starting Node
         * 2. Use a Queue for BFS
         * 3. Maintain a visited Set
         * 4. Add nodes to result in order visited
         */
        
        List<T> result = new ArrayList<>();
        if (!nodes.containsKey(startData)) return result;
        Set<Node<T>> visited = new HashSet<>();
        Queue<Node<T>> q = new LinkedList<>();
        Node<T> start = nodes.get(startData);
        q.add(start);
        visited.add(start);
        while (!q.isEmpty()){
            Node<T> curr = q.poll();
            result.add(curr.data);
            for(int i = 0; i<curr.neighbors.size();i++){
                Node<T> n = curr.neighbors.get(i);
                if(!visited.contains(n)){
                    visited.add(n);
                    q.add(n);
                }
            }
        }
    return result;
    }

    @Override
    public List<T> dfs(T startData) {
        /*
         * TODO:
         * Perform Depth-First Search (recursive or stack version).
         *
         * Steps:
         * 1. Use a Set<Node> to track visited nodes
         * 2. Visit node, then recursively visit neighbors
         */
       
        List<T> result = new ArrayList<>();
        if(!nodes.containsKey(startData)) return result;
        Set<Node<T>> visited = new HashSet<>();
        dfsHelper(nodes.get(startData), visited, result);
        return result;
    }

    private void dfsHelper(Node<T> current, Set<Node<T>> visited, List<T> result) {
        /*
         * TODO:
         * Recursive DFS helper.
         */
        
        visited.add(current);
        result.add(current.data);
        for(int i = 0; i<current.neighbors.size();i++){
            Node<T> n = current.neighbors.get(i);
            if(!visited.contains(n)){
                dfsHelper(n,visited,result);
            }
        }
    }


    @Override
    public List<T> getShortestPath(T startData, T endData) {
        /*
         * TODO:
         * Use BFS to compute shortest path in an unweighted graph.
         *
         * Steps:
         * 1. BFS until reaching end node
         * 2. Reconstruct path by following parent pointers
         * 3. Reverse and return the path
         */
        
        List<T> path = new ArrayList<>();
        if(!nodes.containsKey(startData) || !nodes.containsKey(endData)) return path;
        ArrayList<Node<T>> array = new ArrayList<>(nodes.values());
        for(int i=0;i<array.size();i++){
            array.get(i).visited=false;
            array.get(i).parent=null;
        }
        Queue<Node<T>> q = new LinkedList<>();
        Node<T> start = nodes.get(startData);
        Node<T> end = nodes.get(endData);
        start.visited=true;
        q.add(start);
        while(!q.isEmpty()){
            Node<T> curr = q.poll();
            if(curr == end) break;
            for(int i = 0; i<curr.neighbors.size();i++){
                Node<T> n = curr.neighbors.get(i);
                if(!n.visited){
                    n.visited=true;
                    n.parent=curr;
                    q.add(n);
                }
            }
        }
        Node<T> temp = end;
        while(temp!=null){
            path.add(temp.data);
            temp=temp.parent;
        }
        if(!end.visited) return new ArrayList<>();

        int l =0;
        int r = path.size()-1;
        while(l<r){
            T t = path.get(l);
            path.set(l,path.get(r));
            path.set(r,t);
            l++;
            r--;
        }
        return path;
    }

    public void printGraph() {
        for (T key : nodes.keySet()) {
            System.out.print(key + " -> ");
            Node<T> node = nodes.get(key);
            for (Node<T> neighbor : node.neighbors) {
                System.out.print(neighbor.data + " ");
            }
            System.out.println();
        }
    }
}
