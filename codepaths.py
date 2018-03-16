""" Meager code path measurement tool.
    Ned Batchelder
    http://nedbatchelder.com/blog/200803/python_code_complexity_microtool.html
    MIT License.
"""

import compiler, optparse, sys


class PathNode:
    def __init__(self, name, look="circle"):
        self.name = name
        self.look = look
        
    def to_dot(self):
        return 'node [shape=%s,label="%s"] %d;\n' % (self.look, self.name, self.dot_id())
        
    def dot_id(self):
        return id(self)


class PathGraph:
    def __init__(self, name):
        self.name = name
        self.nodes = {}
    
    def add_node(self, n):
        assert n
        self.nodes.setdefault(n, [])

    def connect(self, n1, n2):
        assert n1
        assert n2
        self.nodes.setdefault(n1, []).append(n2)

    def to_dot(self):
        s = 'subgraph { \n'
        for node in self.nodes:
            s+=node.to_dot()
        for node, nexts in self.nodes.items():
            for next in nexts:
                s+='%s -- %s;\n' % (node.dot_id(), next.dot_id())
        s+='}\n'
		
        return s
		
    def complexity(self):
        """ Return the McCabe complexity for the graph.
            V-E+2
        """
        num_edges = sum([len(n) for n in self.nodes.values()])
        num_nodes = len(self.nodes)
        return num_edges - num_nodes + 2


class PathGraphingAstVisitor(compiler.visitor.ASTVisitor):
    """ A visitor for a parsed Abstract Syntax Tree which finds executable
        statements.
    """

    def __init__(self):
        compiler.visitor.ASTVisitor.__init__(self)
        self.classname = ""
        self.graphs = {}
        self.reset()

    def reset(self):
        self.graph = None
        self.tail = None
        
    def visitFunction(self, node):
        name = "Function %s%s %d" % (self.classname, node.name, node.lineno)
        self.graph = PathGraph(name)
        pathnode = PathNode(name)
        self.tail = pathnode
        self.default(node)
        self.graphs["%s%s" % (self.classname, node.name)] = self.graph
        self.reset()
        
    def visitClass(self, node):
        old_classname = self.classname
        self.classname += node.name + "."
        self.default(node)
        self.classname = old_classname
        
    def appendPathNode(self, name, look='circle'):
        if not self.tail:
            return
        pathnode = PathNode(name, look)
        self.graph.add_node(pathnode)
        self.graph.connect(self.tail, pathnode)
        self.tail = pathnode
        return pathnode
    
    def visitSimpleStatement(self, node):
        name = "Stmt %d" % node.lineno
        self.appendPathNode(name)
    
    visitAssert = visitAssign = visitAssTuple = visitPrint = \
        visitPrintnl = visitRaise = visitSubscript = visitDecorators = \
        visitPass = visitDiscard = visitGlobal = visitReturn = \
        visitSimpleStatement

    def visitLoop(self, node):
        name = "Loop %d" % node.lineno
        pathnode = self.appendPathNode(name)
        self.tail = pathnode
        self.default(node.body)
        bottom = PathNode("", look='point')
        self.graph.connect(self.tail, bottom)
        self.graph.connect(pathnode, bottom)
        self.tail = bottom
        # TODO: else clause in node.else_
        
    visitFor = visitWhile = visitLoop
    
    def visitIf(self, node):
        name = "If %d" % node.lineno
        pathnode = self.appendPathNode(name, 'Mdiamond')
        if not pathnode:
            return  # TODO: figure out what to do with if's outside def's.
        loose_ends = []
        for t, n in node.tests:
            self.tail = pathnode
            self.default(n)
            loose_ends.append(self.tail)
        if node.else_:
            self.tail = pathnode
            self.default(node.else_)
            loose_ends.append(self.tail)
        else:
            loose_ends.append(pathnode)
        bottom = PathNode("", look='point')
        for le in loose_ends:
            self.graph.connect(le, bottom)
        self.tail = bottom
        
    # TODO: visitTryExcept
    # TODO: visitTryFinally
    # TODO: visitWith
            

def main(argv):
    opar = optparse.OptionParser()
    opar.add_option("-d", "--dot", dest="dot", help="output a graphviz dot file", action="store_true")
    opar.add_option("-m", "--min", dest="min", help="minimum complexity for output", type="int", default=2)
    
    options, args = opar.parse_args(argv)
    
    text = open(args[0], "rU").read()+'\n\n'
    ast = compiler.parse(text)
    visitor = PathGraphingAstVisitor()
    visitor.preorder(ast, visitor)
    
    if options.dot:
        print 'graph {'
        for graph in visitor.graphs.values():
            if graph.complexity() >= options.min:
                graph.to_dot()
        print '}'
    else:
        for graph in visitor.graphs.values():
            if graph.complexity() >= options.min:
                print graph.name, graph.complexity()


if __name__ == '__main__':
    main(sys.argv[1:])
