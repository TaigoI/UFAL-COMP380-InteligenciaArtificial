import argparse
from os.path import dirname, abspath, join as joinPath
from dataclasses import dataclass
from copy import deepcopy as copy

# ------------------------------------ UTIL -----------------------------------------


def loadInput(path):
    with open(path, "r", encoding="utf-8") as src:
        return src.read()


def printDict(dictionary: dict, level=0, tabSize=4):
    string = (" "*tabSize*level) + "{\n"
    for key, value in dictionary.items():
        string += (" "*tabSize*(level+1)) + f"\"{key}\" : "
        if (type(value) == dict):
            string += printDict(value, level+1, tabSize)
        else:
            string += str(value)
        string += "\n"

    string += (" "*tabSize*level) + "}"
    return string


def stringFromRule(rule):
    return f"rule: {printDict(rule[0])} -> {str(rule[1])}\n"


def stringFromKnowledge(variable, result):
    return "knowledge:\n    "+str(variable)+" : "+str(result)+"\n"


def parseInput(src):
    rules = []
    knowledge = {}
    nodes = set()

    lines = filter(lambda l: l != "", src.split("\n"))

    for line in lines:
        line = line.replace(" ", "").replace("(", "").replace(")", "")
        if ("->" in line):
            ifStmts, thenStmt = line.split("->")

            ifStmts = ifStmts.split("&")
            stmts = {}
            for s in ifStmts:
                if (s[0] == "!"):
                    nodes.add(s[1:])
                    stmts[s[1:]] = False
                else:
                    nodes.add(s)
                    stmts[s] = True

            if (thenStmt[0] == "!"):
                nodes.add(thenStmt[1:])
                rules.append([stmts, [thenStmt[1:], False]])
            else:
                nodes.add(thenStmt)
                rules.append([stmts, [thenStmt, True]])
        else:
            if (line[0] == "!"):
                nodes.add(line[1:])
                knowledge[line[1:]] = False
            else:
                nodes.add(line)
                knowledge[line] = True

    return rules, knowledge, nodes

# ------------------------------------ TREE -----------------------------------------


NODES_B = {}
NODES_F = {}


@dataclass
class NodeB:
    var: str
    state: bool
    requirements: list[dict]


def buildRuleTree(rules):
    for rule in rules:
        statement, consequence = rule
        NODES_B.append(NodeB(consequence[0], consequence[1], ))


def validateStatement(statement, knowledge):
    for node, requiredValue in statement.items():
        if ((node not in knowledge.keys()) or (knowledge[node] != requiredValue)):
            return False
    return True


# ---------------------------------- FORWARDS ---------------------------------------

def fwdInference(rules, knowledge, nodes, target):
    inference = {}
    rules = copy(rules)
    for node in nodes:
        inference[node] = None

    for statement, value in knowledge.items():
        inference[statement] = value

    changed = copy(nodes)
    while True:
        index = 0
        while index < len(rules):
            statement, consequence = rules[index]
            revalidateRule = False
            for operand in statement.keys():
                if (operand in changed):
                    revalidateRule = True
                    break

            if (not revalidateRule):
                del rules[index]
                index -= 1
            else:
                if validateStatement(statement, inference):
                    changed.add(consequence[0])
                    inference[consequence[0]] = consequence[1]
            index += 1

        if inference[target] != None or len(changed) == 0:
            return inference[target]

        changed = []


# ---------------------------------- BACKWARDS --------------------------------------


def bwdInference(rules, knowledge, nodes, target, visited, unknown):
    inference = {}
    rules = copy(rules)
    for node in nodes:
        inference[node] = None

    for statement, value in knowledge.items():
        inference[statement] = value

    if (inference[target] != None):
        return inference[target]

    index = 0
    targetIsConsequence = False
    while index < len(rules):
        statement, consequence = rules[index]
        if (target == consequence[0] and len([s for s in statement.keys() if s in unknown]) == 0):
            targetIsConsequence = True
            if validateStatement(statement, inference):
                return consequence[1]
            else:
                for newTarget in statement.keys():
                    if (target not in visited):
                        v2 = copy(visited)
                        v2.append(target)
                        result = bwdInference(
                            rules, knowledge, nodes, newTarget, v2, unknown)
                        if (result == None):
                            break
                        elif (result != statement[newTarget]):
                            knowledge[newTarget] = result
                            break
                        else:
                            inference[newTarget] = result
                            knowledge[newTarget] = result
                            print(
                                f"\n... Adicionando {newTarget} = {result} na mem??ria de trabalho\n")
                            index -= 1
                for statement, value in knowledge.items():
                    inference[statement] = value

        index += 1

    if not targetIsConsequence:
        print("\n\n-------------------- Infer (Backchaining Data Request) --------------------")
        print(
            f"\nN??o h?? regra resultante em {target},\nvoc?? conhece o valor de {target}?")
        knows = lerSimOuNao()
        if (knows):
            print(f"{target} = ", end="")
        else:
            unknown.append(target)

        return lerVerdadeiroOuFalso() if knows else None

# ------------------------------------ MAIN -----------------------------------------


def lerSimOuNao() -> bool:
    print("\n")
    print("    [0] N??o")
    print("    [1] Sim")

    a: str = input("\nA????o: ")
    while ((not a.isdigit()) or (a.isdigit() and int(a) not in (0, 1))):
        a = input("\nA????o inv??lida, escolha entre \"0\" e \"1\"")
    print("\n")
    return int(a) == 1


def lerVerdadeiroOuFalso() -> bool:
    print("\n")
    print("    [0] Falso (False)")
    print("    [1] Verdadeiro (True)")

    a: str = input("\nA????o: ")
    while ((not a.isdigit()) or (a.isdigit() and int(a) not in (0, 1))):
        a = input("\nA????o inv??lida, escolha entre \"0\" e \"1\"")
    print("\n")
    return int(a) == 1


def addMenu():
    print("\n\n---------------------------- Add Knowledge|Rule -----------------------------")
    print("Knowledge ex.: \"Cancer\" ou \"!Cancer\"")
    print("Rule ex.: \"!Pain & PaleSkin\" -> Cancer\"")
    a: str = input("\nInput: ")
    return parseInput(a)


def inferMenu(nodes):
    nodes = list(nodes)
    nodes.sort()

    print("\n\n---------------------------------- Infer ----------------------------------")
    for index, node in enumerate(nodes):
        print(f"    [{index:2.0f}] {node}")

    a: str = input("\nA????o: ")
    while ((not a.isdigit()) or (a.isdigit() and int(a) not in range(len(nodes)))):
        a = input(
            f"\nA????o inv??lida, escolha um valor de \"0\" a \"{len(nodes)-1}\": ")
    return nodes[int(a)]


def menu():
    print("\n\n--------------------------------- Engenho ---------------------------------")
    print("    [0] Infer")
    print("    [1] Add or Update Knowledge|Rule")
    print("    [2] Show Memory")
    print("    [3] Clear Knowledge")
    print("    [4] Quit")

    a: str = input("\nA????o: ")
    while ((not a.isdigit()) or (a.isdigit() and int(a) not in (range(5)))):
        a = input("\nA????o inv??lida, escolha entre \"0\" a \"4\": ")
    return int(a)


def showMemory(rules, knowledge, nodes):
    print("\n\n--------------------------------- Memory ----------------------------------")
    print("\n".join(map(stringFromRule, rules)))
    print("\n".join([stringFromKnowledge(k, v)
                     for k, v in knowledge.items()]))

    sNodes = '\n    '.join(sorted(list(nodes)))
    print(f"Nodes: (\n    {sNodes}\n)")


def main(input):
    try:
        src = loadInput(input)
    except:
        print("\nErro: N??o foi poss??vel ler o arquivo selecionado.\n"
              + "      Verifique se o caminho est?? correto...\n")
    else:
        rules, knowledge, nodes = parseInput(src)
        showMemory(rules, knowledge, nodes)

        m = menu()
        while (m != 4):
            if (m == 0):
                node = inferMenu(nodes)
                inf = fwdInference(rules, knowledge, nodes, node)
                if inf == None:
                    inf = bwdInference(
                        rules, knowledge, nodes, node, list(), list())
                print(f"Infer??ncia de {node} resultou em {inf}" if inf !=
                      None else f"N??o foi poss??vel inferir {node}")

            elif (m == 1):
                newRules, newKnowledge, newNodes = addMenu()

                printed = False
                print("\n -> NEW <- \n")

                if (len(newRules) > 0):
                    printed = True
                    print("\n".join(map(stringFromRule, newRules)))

                if (len(newKnowledge.keys()) > 0):
                    printed = True
                    print("\n".join([stringFromKnowledge(k, v)
                                     for k, v in newKnowledge.items()]))
                if (len([n for n in newNodes if n not in nodes]) > 0):
                    printed = True
                    print(
                        f"Nodes: ({','.join([n for n in newNodes if n not in nodes])})")

                if (not printed):
                    print("nothing...\n")

                rules.extend(newRules)
                knowledge.update(newKnowledge)
                nodes.update(newNodes)

            elif (m == 2):
                showMemory(rules, knowledge, nodes)

            elif (m == 3):
                knowledge = {}

            m = menu()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Engenho de Infer??ncia e Base de Conhecimento\n'
        + '     Apresentado ao Prof. Evandro Costa\n'
        + ' 2022.1 - COMP380 - INTELIG??NCIA ARTIFICIAL\n\n'
        + 'Por: Ta??go I. M. Pedrosa\n\n\n'
        + 'Verifique a entrada esperada em ./input.txt\n\n\n',
        formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-i', '--input', metavar='INPUT', dest='input',
                        help='Sets the input file\'s path.\n'
                        + 'If input isn\'t set, it will be requested interactively.')
    args = parser.parse_args()

    if (not args.input):
        print("\nQuest??o 2\n(mesmo motor interativo, com forward e backward chaining, que Quest??o 1)\n")
        print("\nInstru????es de formata????o\n")
        print("1 - Um item ?? verdadeiro se n??o possui \"!\" no in??cio de seu nome.\n    Ex.: \"Covid19\" equivale a \"Covid19 = True\"\n")
        print("2 - Um item n??o ?? verdadeiro se possui \"!\" no in??cio de seu nome.\n    Ex.: \"!Covid19\" equivale a \"Covid19 = False\"\n")
        print("3 - Uma linha ?? regra se possui o operador \"->\" (implica)\n    O operador ?? usado para dividir a frase em clausula SE e consequ??ncia ENT??O\n")
        print("4 - Uma regra pode ter v??rios itens (separados por \"&\") na sua clausula SE.\n    Ex.: \"Gripe & !ContatoComCovid19 -> !Covid19\"\n    Ex.2: \"Gripe & ContatoComCovid19 -> Covid19\"\n")
        print("5 - Uma regra s?? pode ter uma consequ??ncia ENT??O.\n    Ex. v??lido: \"Gripe & !ContatoComCovid19 -> !Covid19\"\n    Ex. Inv??lido: \"Gripe & ContatoComCovid19 -> Covid19 & RiscoInterna????o\"\n")

        prompt = input("\nPath (ou Enter para usar padr??o): ")
        if (prompt != ""):
            args.input = prompt
        else:
            args.input = joinPath(dirname(abspath(__file__)), "questao2.data")
            print(f'No path provided, using default {args.input}\n')

    main(input=args.input)
