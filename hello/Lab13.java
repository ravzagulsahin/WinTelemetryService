import java.util.*;

public class Lab13 {

    public static void main(String[] args) {
        Graph<String> g = new Graph<>();

        g.addEdge("A", "B", 1);
        g.addEdge("A", "C", 4);
        g.addEdge("B", "C", 2);
        g.addEdge("C", "D", 1);

        System.out.println(g.greedyWalk("A", "D"));
        System.out.println(g.dijkstra("A", "D"));

        Graph<String> mst = g.mstPrims("A");
        mst.printEdges();
    }
}

class Edge<T> {
    Node<T> target;
    int weight;

    public Edge(Node<T> target, int weight) {
        this.target = target;
        this.weight = weight;
    }
}

class Node<T> implements Comparable<Node<T>> {
    T data;
    List<Edge<T>> edges;

    Node<T> parent;
    int gCost;

    public Node(T data) {
        this.data = data;
        edges = new ArrayList<>();
        gCost = Integer.MAX_VALUE;
    }

    public void addNeighbor(Node<T> target, int weight) {
        edges.add(new Edge<>(target, weight));
    }

    @Override
    public int compareTo(Node<T> o) {
        return Integer.compare(this.gCost, o.gCost);
    }

    @Override
    public String toString() {
        return data.toString();
    }
}

class Graph<T> {
    private Map<T, Node<T>> nodes;

    public Graph() {
        nodes = new HashMap<>();
    }

    // Adds a node if it doesn't exist
    public void addNode(T data) {
        if (!nodes.containsKey(data)) {
            nodes.put(data, new Node<>(data));
        }
    }

    // Adds an undirected edge
    public void addEdge(T data1, T data2, int weight) {
        addNode(data1);
        addNode(data2);

        Node<T> n1 = nodes.get(data1);
        Node<T> n2 = nodes.get(data2);

        n1.addNeighbor(n2, weight);
        n2.addNeighbor(n1, weight);
    }

    // Prints edges for debugging MST
    public void printEdges() {
        Object[] keys = nodes.keySet().toArray();

        for (int i = 0; i < keys.length; i++) {
            Node<T> n = nodes.get(keys[i]);

            for (int j = 0; j < n.edges.size(); j++) {
                Edge<T> e = n.edges.get(j);

                if (n.data.hashCode() < e.target.data.hashCode()) {
                    System.out.println(n.data + " - " + e.target.data + " : " + e.weight);
                }
            }
        }
    }

    // Task: Implement a greedy search. 
    // Always pick the cheapest *immediate* neighbor.
    // Handles dead ends by stopping.
    public List<T> greedyWalk(T startData, T endData) {

        // TODO: Implement Greedy Walk
        // 1. Create a Queue and a Visited Set
        // 2. Loop while queue is not empty
        // 3. Inside loop: Find the neighbor with the LOWEST edge weight
        // 4. Move to that neighbor (set parent, add to queue)
        // 5. If found end, return reconstructPath(current)

        Queue<Node<T>> queue = new LinkedList<>();
        Set<Node<T>> visited = new HashSet<>();

        Node<T> start = nodes.get(startData);
        Node<T> end = nodes.get(endData);

        if (start == null || end == null)
            return null;

        start.parent = null;
        queue.add(start);

        while (!queue.isEmpty()) {
            Node<T> current = queue.poll();
            visited.add(current);

            if (current == end) {
                return reconstructPath(current);
            }

            Edge<T> cheapest = null;

            for (int i = 0; i < current.edges.size(); i++) {
                Edge<T> e = current.edges.get(i);

                if (!visited.contains(e.target)) {
                    if (cheapest == null || e.weight < cheapest.weight) {
                        cheapest = e;
                    }
                }
            }

            if (cheapest == null)
                break;

            cheapest.target.parent = current;
            queue.add(cheapest.target);
        }

        return null;
    }

    // Task: Implement Dijkstra to find the true shortest path.
    // Use a PriorityQueue to explore the globally cheapest path
    public List<T> dijkstra(T startData, T endData) {

        Node<T> start = nodes.get(startData);
        Node<T> end = nodes.get(endData);

        if (start == null || end == null)
            return null;

        Object[] keys = nodes.keySet().toArray();
        for (int i = 0; i < keys.length; i++) {
            Node<T> n = nodes.get(keys[i]);
            n.gCost = Integer.MAX_VALUE;
            n.parent = null;
        }

        start.gCost = 0;

        PriorityQueue<Node<T>> pq = new PriorityQueue<>();
        Set<Node<T>> visited = new HashSet<>();

        pq.add(start);

        while (!pq.isEmpty()) {
            Node<T> current = pq.poll();

            if (visited.contains(current))
                continue;

            visited.add(current);

            if (current == end) {
                return reconstructPath(current);
            }

            for (int i = 0; i < current.edges.size(); i++) {
                Edge<T> e = current.edges.get(i);
                Node<T> neighbor = e.target;

                int newCost = current.gCost + e.weight;

                if (newCost < neighbor.gCost) {
                    neighbor.gCost = newCost;
                    neighbor.parent = current;
                    pq.add(neighbor);
                }
            }
        }

        return null;
    }

    // Task: Return a NEW Graph representing the Minimum Spanning Tree.
    public Graph<T> mstPrims(T startData) {

        Node<T> start = nodes.get(startData);
        if (start == null)
            return null;

        Graph<T> mst = new Graph<>();

        Object[] keys = nodes.keySet().toArray();
        for (int i = 0; i < keys.length; i++) {
            Node<T> n = nodes.get(keys[i]);
            n.gCost = Integer.MAX_VALUE;
            n.parent = null;
        }

        start.gCost = 0;

        PriorityQueue<Node<T>> pq = new PriorityQueue<>();
        Set<Node<T>> visited = new HashSet<>();

        pq.add(start);

        while (!pq.isEmpty()) {
            Node<T> current = pq.poll();

            if (visited.contains(current))
                continue;

            visited.add(current);
            mst.addNode(current.data);

            if (current.parent != null) {
                mst.addEdge(current.parent.data, current.data, current.gCost);
            }

            for (int i = 0; i < current.edges.size(); i++) {
                Edge<T> e = current.edges.get(i);
                Node<T> neighbor = e.target;

                if (!visited.contains(neighbor) && e.weight < neighbor.gCost) {
                    neighbor.gCost = e.weight;
                    neighbor.parent = current;
                    pq.add(neighbor);
                }
            }
        }

        return mst;
    }

    // Helper: Backtracks from end node to start using parent pointers
    private List<T> reconstructPath(Node<T> end) {
        List<T> list = new ArrayList<>();
        Node<T> current = end;

        while (current != null) {
            list.add(current.data);
            current = current.parent;
        }

        Collections.reverse(list);
        return list;
    }
}
