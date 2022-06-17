import functools
from collections import deque


class NodeNotFoundError(Exception):
    pass


class TreeIsNoneError(Exception):
    pass


class Node:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

        self.children = list()


def tree_verify(func):
    @functools.wraps(func)
    def inner(self, *args, **kwargs):
        if self.root is None:
            raise TreeIsNoneError()

        return func(self, *args, **kwargs)

    return inner


class Tree:
    def __init__(self, root=None):
        self.root = root

    @tree_verify
    def level_order(self):
        """
        层序遍历
        :return:
        """
        result = [self.root]
        q = deque([self.root])

        while q:
            last_node = q.popleft()
            for ch in last_node.children:
                result.append(ch)
                q.append(ch)

        return result

    @tree_verify
    def find_parent_node(self, node):
        if node == self.root:
            return 0, None

        q = deque([self.root])

        while q:
            last_node = q.popleft()
            for i, ch in enumerate(last_node.children):
                if ch == node:
                    return i, last_node
                q.append(ch)

        raise NodeNotFoundError('node not found:\n{}'.format(node))

    @tree_verify
    def get_level(self, root, node, level=0):
        """
        获得当前结点所在层级
        :param root: 用于遍历的结点
        :param node: 带查找结点
        :param level: 层级，根结点值为0
        :return:
        """
        if root == node:
            return level

        for ch in root.children:
            res = self.get_level(ch, node, level + 1)
            if res != 0:
                return res
        else:
            return 0

    @tree_verify
    def insert(self, p_node, node):
        """
        插入结点
        :param p_node: 待插入结点的父结点
        :param node: 待插入结点
        :return:
        """
        p_node.children.append(node)

        while p_node != self.root:
            try:
                pi, pp_node = self.find_parent_node(p_node)
                pp_node.children[pi] = p_node
                p_node = pp_node
            except NodeNotFoundError:
                return False

        self.root = p_node
        return True

    @tree_verify
    def pre_order(self):
        res = []
        stack = [self.root]

        while stack:
            root = stack.pop()
            res.append(root)

            for ch in root.children[::-1]:
                stack.append(ch)

        return res

    def to_dict(self, attr_name='text'):

        def _to_dict(root: Node, t_dict: dict):
            if not root.children:
                return

            for child in root.children:
                value = getattr(child, attr_name)
                if value not in t_dict:
                    t_dict[value] = {}
                    _to_dict(child, t_dict[value])
                else:
                    _to_dict(child, t_dict[value])

        res = dict()
        _to_dict(self.root, res)

        return res

    @tree_verify
    def update(self, node, **kwargs):
        """
        更新结点的值
        :param node: 待更新结点
        :param kwargs: 待更新的属性
        :return:
        """
        for k, v in kwargs.items():
            setattr(node, k, v)

        while node != self.root:
            try:
                i, p_node = self.find_parent_node(node)
                if p_node is None:
                    break
                p_node.children[i] = node
                node = p_node
            except NodeNotFoundError:
                return False

        self.root = node
        return True


def test():
    nodes = [Node(value=i) for i in range(13)]
    nodes[0].children = nodes[1:4]
    nodes[0].children[0].children = nodes[4:8]
    nodes[0].children[1].children = nodes[8:10]
    nodes[0].children[2].children = nodes[10:12]
    nodes[0].children[0].children[1].children = [nodes[12]]

    tree = Tree(nodes[0])
    # print(tree.get_level(nodes[0], nodes[3]))
    # print(tree.level_order())
    # node = tree.find_parent_node(node=nodes[1])
    tree.update(nodes[12], value=15)
    res = [obj.value for obj in tree.level_order()]
    print(tree.to_dict())
    # print(res)
    # print(tree.get_level(nodes[0], insert_node))


if __name__ == '__main__':
    test()
